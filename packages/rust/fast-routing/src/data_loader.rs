use crate::{RoutingResult, RoutingError, network::{Network, Node, Edge, NodeId, EdgeId, RoutingMode}};
use polars::prelude::*;
use geo_types::{LineString, Point};
use std::collections::HashMap;
use wkt::TryFromWkt;

/// Loader for real-world network data from Parquet files
pub struct NetworkLoader;

impl NetworkLoader {
    /// Load network from Parquet file with OSM-style schema
    pub fn load_from_parquet(file_path: &str) -> RoutingResult<Network> {
        log::info!("Loading network from Parquet file: {}", file_path);
        
        // Use the simplified Parquet file by default
        let simple_path = file_path.replace("network.parquet", "network_simple.parquet");
        let parquet_path = if std::path::Path::new(&simple_path).exists() {
            &simple_path
        } else {
            file_path
        };
        
        log::info!("Using Parquet file: {}", parquet_path);
        
        // Read the Parquet file using Polars
        let df = LazyFrame::scan_parquet(parquet_path, ScanArgsParquet::default())
            .map_err(|e| RoutingError::Network(format!("Failed to read Parquet file: {}", e)))?
            .collect()
            .map_err(|e| RoutingError::Network(format!("Failed to collect data: {}", e)))?;
        
        log::info!("Loaded {} edges from Plan4Better Munich network", df.height());
        
        // Extract required columns - Plan4Better network uses 'edge_id' 
        let edge_ids = df.column("edge_id")
            .map_err(|e| RoutingError::Network(format!("Missing 'edge_id' column: {}", e)))?
            .i32()
            .map_err(|e| RoutingError::Network(format!("Invalid 'edge_id' column type: {}", e)))?;
            
        let sources = df.column("source")
            .map_err(|e| RoutingError::Network(format!("Missing 'source' column: {}", e)))?
            .i32()  // Changed from i64 to i32 based on data inspection
            .map_err(|e| RoutingError::Network(format!("Invalid 'source' column type: {}", e)))?;
            
        let targets = df.column("target")
            .map_err(|e| RoutingError::Network(format!("Missing 'target' column: {}", e)))?
            .i32()  // Changed from i64 to i32 based on data inspection
            .map_err(|e| RoutingError::Network(format!("Invalid 'target' column type: {}", e)))?;
            
        let lengths = df.column("length_m")
            .map_err(|e| RoutingError::Network(format!("Missing 'length_m' column: {}", e)))?
            .f64()
            .map_err(|e| RoutingError::Network(format!("Invalid 'length_m' column type: {}", e)))?;
            
        // Try to get geometry column (could be "geom" or "geometry")
        let geometries = df.column("geometry")
            .or_else(|_| df.column("geom"))
            .map_err(|e| RoutingError::Network(format!("Missing geometry column (geom/geometry): {}", e)))?
            .str()
            .map_err(|e| RoutingError::Network(format!("Invalid geometry column type: {}", e)))?;
        
        // Create network
        let mut network = Network::new();
        let mut node_coordinates: HashMap<NodeId, Point<f64>> = HashMap::new();
        
        // First pass: extract all unique nodes and their coordinates from geometries
        log::info!("Extracting node coordinates from geometries...");
        
        for i in 0..df.height() {
            if let (Some(source_id), Some(target_id), Some(geom_str)) = (
                sources.get(i),
                targets.get(i),
                geometries.get(i)
            ) {
                // Parse WKT geometry
                if let Ok(geom) = LineString::<f64>::try_from_wkt_str(geom_str) {
                    let coords = geom.coords().collect::<Vec<_>>();
                    if coords.len() >= 2 {
                        // Source node coordinate (first point)
                        let source_point = Point::new(coords[0].x, coords[0].y);
                        let target_point = Point::new(coords.last().unwrap().x, coords.last().unwrap().y);
                        
                        node_coordinates.insert(source_id as NodeId, source_point);
                        node_coordinates.insert(target_id as NodeId, target_point);
                    }
                } else {
                    log::warn!("Failed to parse geometry for edge {}: {}", i, geom_str);
                }
            }
        }
        
        log::info!("Found {} unique nodes", node_coordinates.len());
        
        // Add nodes to network
        for (&node_id, &point) in &node_coordinates {
            let node = Node::new(node_id, point.x(), point.y());
            network.add_node(node)?;
        }
        
        // Second pass: add edges
        log::info!("Adding edges to network...");
        let mut added_edges = 0;
        
        for i in 0..df.height() {
            if let (Some(edge_id), Some(source_id), Some(target_id), Some(length), Some(geom_str)) = (
                edge_ids.get(i),
                sources.get(i),
                targets.get(i),
                lengths.get(i),
                geometries.get(i),
            ) {
                // Parse geometry
                if let Ok(linestring) = LineString::<f64>::try_from_wkt_str(geom_str) {
                    // Create edge
                    let edge = Edge::new(
                        edge_id as EdgeId,
                        source_id as NodeId,
                        target_id as NodeId,
                        linestring,
                        length,
                    );
                    
                    // Add edge with walking routing mode for pedestrian analysis
                    network.add_edge(edge, RoutingMode::Walking)?;
                    added_edges += 1;
                } else {
                    log::warn!("Failed to parse geometry for edge {}", edge_id);
                }
            }
        }
        
        log::info!("Successfully added {} edges to network", added_edges);
        log::info!("Network created with {} nodes and {} edges", 
                  network.node_count(), network.edge_count());
        
        Ok(network)
    }
    
    /// Load test points from Parquet file
    pub fn load_test_points(parquet_path: &str) -> RoutingResult<Vec<NodeId>> {
        log::info!("Loading test points from: {}", parquet_path);
        
        let df = LazyFrame::scan_parquet(parquet_path, ScanArgsParquet::default())
            .map_err(|e| RoutingError::Network(format!("Failed to read test points: {}", e)))?
            .collect()
            .map_err(|e| RoutingError::Network(format!("Failed to collect test points: {}", e)))?;
        
        let node_ids = df.column("node_id")
            .map_err(|e| RoutingError::Network(format!("Missing 'node_id' column: {}", e)))?
            .i32()  // Changed from i64 to i32
            .map_err(|e| RoutingError::Network(format!("Invalid 'node_id' column type: {}", e)))?;
        
        let test_points: Vec<NodeId> = node_ids.iter()
            .filter_map(|id| id.map(|v| v as NodeId))
            .collect();
        
        log::info!("Loaded {} test points", test_points.len());
        Ok(test_points)
    }
}