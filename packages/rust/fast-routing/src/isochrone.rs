use crate::{RoutingResult, ContractionHierarchy, network::{NodeId, Cost, Network}};
use std::collections::{HashMap, BinaryHeap};
use serde::{Deserialize, Serialize};
use petgraph::visit::EdgeRef;
use std::cmp::Ordering;
use polars::prelude::*;

/// Result of isochrone calculation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IsochroneResult {
    /// Travel costs for each reachable node
    pub travel_costs: HashMap<NodeId, Cost>,
    /// Maximum cost used in calculation
    pub max_cost: Cost,
    /// Number of reachable nodes
    pub reachable_nodes: usize,
    /// Starting node ID
    pub start_node: NodeId,
}

/// State for Dijkstra-based isochrone calculation
#[derive(Debug, Clone, PartialEq)]
struct IsochroneState {
    node: NodeId,
    cost: Cost,
}

impl Eq for IsochroneState {}

impl Ord for IsochroneState {
    fn cmp(&self, other: &Self) -> Ordering {
        other.cost.partial_cmp(&self.cost).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for IsochroneState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Enhanced isochrone calculator for real catchment areas
pub struct IsochroneCalculator;

impl IsochroneCalculator {
    /// Calculate detailed isochrone from a starting node
    pub fn calculate(
        ch: &ContractionHierarchy,
        start_node_id: NodeId,
        max_cost: Cost,
    ) -> RoutingResult<IsochroneResult> {
        log::info!("Calculating isochrone from node {} with max cost {:.0}s ({:.1} min)", start_node_id, max_cost, max_cost/60.0);
        
        // Perform Dijkstra search to find all reachable nodes within cost limit
        let travel_costs = Self::dijkstra_isochrone(ch, start_node_id, max_cost)?;
        
        let reachable_nodes = travel_costs.len();
        log::info!("Found {} reachable nodes within {:.0}s ({:.1} min) travel time", reachable_nodes, max_cost, max_cost/60.0);
        
        Ok(IsochroneResult {
            travel_costs,
            max_cost,
            reachable_nodes,
            start_node: start_node_id,
        })
    }
    
    /// Dijkstra-based search to find all reachable nodes within cost limit
    fn dijkstra_isochrone(
        ch: &ContractionHierarchy,
        start_node_id: NodeId,
        max_cost: Cost,
    ) -> RoutingResult<HashMap<NodeId, Cost>> {
        let _start_idx = ch.original_network.get_node_index(start_node_id)
            .ok_or_else(|| crate::RoutingError::Network(format!("Start node {} not found", start_node_id)))?;
        
        let mut distances = HashMap::new();
        let mut heap = BinaryHeap::new();
        
        // Initialize with start node
        distances.insert(start_node_id, 0.0);
        heap.push(IsochroneState { node: start_node_id, cost: 0.0 });
        
        while let Some(IsochroneState { node: current_node_id, cost: current_cost }) = heap.pop() {
            // Skip if we've already processed this node with a better cost
            if let Some(&best_cost) = distances.get(&current_node_id) {
                if current_cost > best_cost {
                    continue;
                }
            }
            
            // Skip if cost exceeds limit
            if current_cost > max_cost {
                continue;
            }
            
            // Find the node index for this node ID
            if let Some(current_idx) = ch.original_network.get_node_index(current_node_id) {
                // Explore neighbors
                for edge in ch.original_network.graph.edges(current_idx) {
                    let neighbor_idx = edge.target();
                    let edge_cost = edge.weight().cost;
                    let new_cost = current_cost + edge_cost;
                    
                    // Skip if exceeds max cost
                    if new_cost > max_cost {
                        continue;
                    }
                    
                    // Get neighbor node data
                    if let Some(neighbor_node) = ch.original_network.graph.node_weight(neighbor_idx) {
                        let neighbor_id = neighbor_node.id;
                        
                        // Check if this is a better path to the neighbor
                        let is_better = match distances.get(&neighbor_id) {
                            Some(&existing_cost) => new_cost < existing_cost,
                            None => true,
                        };
                        
                        if is_better {
                            distances.insert(neighbor_id, new_cost);
                            heap.push(IsochroneState { node: neighbor_id, cost: new_cost });
                        }
                    }
                }
            }
        }
        
        log::debug!("Dijkstra isochrone found {} reachable nodes", distances.len());
        Ok(distances)
    }
    
    /// Export isochrone results as geoparquet with node coordinates
    pub fn export_as_geoparquet(
        results: &[(NodeId, Vec<IsochroneResult>)],
        network: &Network,
        output_path: &str,
    ) -> RoutingResult<()> {
        log::info!("Exporting {} isochrone results as geoparquet to {}", results.len(), output_path);
        
        // Collect all network data
        let mut records = Vec::new();
        
        for (start_node, node_results) in results {
            for result in node_results {
                for (reachable_node_id, travel_cost) in &result.travel_costs {
                    // Get node coordinates from network
                    if let Some(node) = network.get_node(*reachable_node_id) {
                        records.push((
                            *start_node as i64,
                            result.max_cost,
                            result.max_cost / 60.0, // minutes
                            *reachable_node_id as i64,
                            *travel_cost,
                            *travel_cost / 60.0, // minutes
                            node.location.x(),
                            node.location.y(),
                        ));
                    }
                }
            }
        }
        
        log::info!("Collected {} reachable node records", records.len());
        
        // Create DataFrame
        let df = df! {
            "start_node" => records.iter().map(|r| r.0).collect::<Vec<_>>(),
            "max_cost_seconds" => records.iter().map(|r| r.1).collect::<Vec<_>>(),
            "max_cost_minutes" => records.iter().map(|r| r.2).collect::<Vec<_>>(),
            "reachable_node" => records.iter().map(|r| r.3).collect::<Vec<_>>(),
            "travel_cost_seconds" => records.iter().map(|r| r.4).collect::<Vec<_>>(),
            "travel_cost_minutes" => records.iter().map(|r| r.5).collect::<Vec<_>>(),
            "longitude" => records.iter().map(|r| r.6).collect::<Vec<_>>(),
            "latitude" => records.iter().map(|r| r.7).collect::<Vec<_>>(),
        }.map_err(|e| crate::RoutingError::Network(format!("Failed to create DataFrame: {}", e)))?;
        
        // Export as regular parquet (we'll handle geoparquet conversion in Python)
        let mut file = std::fs::File::create(output_path)
            .map_err(|e| crate::RoutingError::Network(format!("Failed to create output file: {}", e)))?;
        
        ParquetWriter::new(&mut file)
            .finish(&mut df.clone())
            .map_err(|e| crate::RoutingError::Network(format!("Failed to write parquet: {}", e)))?;
        
        log::info!("Successfully exported network data to {}", output_path);
        Ok(())
    }
    
    /// Calculate multiple isochrones for different cost thresholds
    pub fn calculate_multiple(
        ch: &ContractionHierarchy,
        start_node_id: NodeId,
        cost_thresholds: &[Cost],
    ) -> RoutingResult<Vec<IsochroneResult>> {
        let mut results = Vec::new();
        
        for &max_cost in cost_thresholds {
            let result = Self::calculate(ch, start_node_id, max_cost)?;
            results.push(result);
        }
        
        Ok(results)
    }
}