use crate::{RoutingError, RoutingResult, network::{Network, NodeId, Cost}};
use petgraph::graph::NodeIndex;
use petgraph::visit::EdgeRef;
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Ordering;

/// State for Dijkstra search
#[derive(Debug, Clone, PartialEq)]
struct DijkstraState {
    node: NodeIndex,
    cost: Cost,
}

impl Eq for DijkstraState {}

impl Ord for DijkstraState {
    fn cmp(&self, other: &Self) -> Ordering {
        other.cost.partial_cmp(&self.cost).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for DijkstraState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Simplified Contraction Hierarchy (actually just uses Dijkstra for now)
#[derive(Debug)]
pub struct ContractionHierarchy {
    /// Original network
    pub original_network: Network,
}

impl ContractionHierarchy {
    /// Build contraction hierarchy from network (simplified)
    pub fn new(network: Network) -> RoutingResult<Self> {
        Ok(Self {
            original_network: network,
        })
    }

    /// Get stats about the hierarchy
    pub fn stats(&self) -> HashMap<String, String> {
        let mut stats = HashMap::new();
        stats.insert("nodes".to_string(), self.original_network.node_count().to_string());
        stats.insert("edges".to_string(), self.original_network.edge_count().to_string());
        stats.insert("algorithm".to_string(), "Dijkstra".to_string());
        stats
    }

    /// Perform shortest path search using basic Dijkstra
    pub fn shortest_path(&self, from_node_id: NodeId, to_node_id: NodeId) -> RoutingResult<Option<(Cost, Vec<NodeId>)>> {
        // Find node indices in original network
        let from_idx = self.original_network.get_node_index(from_node_id)
            .ok_or_else(|| RoutingError::Network(format!("Node {} not found", from_node_id)))?;
        let to_idx = self.original_network.get_node_index(to_node_id)
            .ok_or_else(|| RoutingError::Network(format!("Node {} not found", to_node_id)))?;

        // Simple Dijkstra
        self.dijkstra_search(from_idx, to_idx)
    }

    /// Simple Dijkstra implementation
    fn dijkstra_search(
        &self,
        from_idx: NodeIndex,
        to_idx: NodeIndex,
    ) -> RoutingResult<Option<(Cost, Vec<NodeId>)>> {
        let mut distances = HashMap::new();
        let mut predecessors = HashMap::new();
        let mut heap = BinaryHeap::new();

        distances.insert(from_idx, 0.0);
        heap.push(DijkstraState { node: from_idx, cost: 0.0 });

        while let Some(DijkstraState { node, cost }) = heap.pop() {
            if node == to_idx {
                // Reconstruct path
                let mut path = Vec::new();
                let mut current = to_idx;
                
                while let Some(&pred) = predecessors.get(&current) {
                    if let Some(node_data) = self.original_network.graph.node_weight(current) {
                        path.push(node_data.id);
                    }
                    current = pred;
                }
                
                if let Some(node_data) = self.original_network.graph.node_weight(from_idx) {
                    path.push(node_data.id);
                }
                
                path.reverse();
                return Ok(Some((cost, path)));
            }

            if cost > *distances.get(&node).unwrap_or(&f64::INFINITY) {
                continue;
            }

            for edge in self.original_network.graph.edges(node) {
                let neighbor = edge.target();
                let edge_cost = edge.weight().cost;
                let new_cost = cost + edge_cost;

                if new_cost < *distances.get(&neighbor).unwrap_or(&f64::INFINITY) {
                    distances.insert(neighbor, new_cost);
                    predecessors.insert(neighbor, node);
                    heap.push(DijkstraState { node: neighbor, cost: new_cost });
                }
            }
        }

        Ok(None)
    }

    /// Get network statistics (detailed version)
    pub fn detailed_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        stats.insert("original_nodes".to_string(), self.original_network.node_count());
        stats.insert("original_edges".to_string(), self.original_network.edge_count());
        stats.insert("shortcuts_created".to_string(), 0); // Simplified version
        stats
    }
}