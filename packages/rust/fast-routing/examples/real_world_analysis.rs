use fast_routing::{NetworkLoader, ContractionHierarchy, IsochroneCalculator, RoutingResult};

fn main() -> RoutingResult<()> {
    env_logger::init();
    
    println!("=== Real-World Walking Catchment Area Analysis ===");
    
    // Load network from Parquet
    println!("\n1. Loading network from Parquet...");
    let network_path = "data/network.parquet";
    let network = NetworkLoader::load_from_parquet(network_path)?;
    
    println!("✓ Network loaded: {} nodes, {} edges", 
             network.node_count(), 
             network.edge_count());
    println!("  Speed: 5 km/h (walking mode)");
    
    // Build contraction hierarchy
    println!("\n2. Building contraction hierarchy...");
    let ch = ContractionHierarchy::new(network)?;
    let stats = ch.stats();
    
    println!("✓ Contraction hierarchy built");
    for (key, value) in stats {
        println!("  {}: {}", key, value);
    }
    
    // Load test points
    println!("\n3. Loading test points...");
    let test_points_path = "data/parquet/test_points.parquet";
    let test_points = NetworkLoader::load_test_points(test_points_path)?;
    
    println!("✓ Loaded {} test points", test_points.len());
    for (i, &node_id) in test_points.iter().enumerate() {
        println!("  Test point {}: Node {}", i + 1, node_id);
    }
    
    // Calculate catchment areas for multiple cost thresholds
    println!("\n4. Calculating walking catchment areas...");
    
    let cost_thresholds = vec![300.0, 600.0, 900.0, 1200.0]; // Travel time in seconds (5, 10, 15, 20 minutes)
    let mut all_results = Vec::new();
    
    for (i, &start_node) in test_points.iter().enumerate() {
        println!("\n--- Test Point {} (Node {}) ---", i + 1, start_node);
        
        let mut point_results = Vec::new();
        
        for &max_cost in &cost_thresholds {
                match IsochroneCalculator::calculate(&ch, start_node, max_cost) {
                Ok(result) => {
                    println!("  {:.0}s ({:.1}min): {} reachable nodes", 
                            max_cost, max_cost/60.0,
                            result.reachable_nodes);
                    
                    point_results.push(result);
                },
                Err(e) => {
                    println!("  {:.0}s: Error - {}", max_cost, e);
                }
            }
        }
        
        all_results.push((start_node, point_results));
    }
    
    // Export results as geoparquet with coordinates
    println!("\n5. Exporting results as geoparquet...");
    let output_path = "data/results/walking_network.parquet";
    
    // Create results directory
    std::fs::create_dir_all("data/results").map_err(|e| 
        fast_routing::RoutingError::Network(format!("Failed to create results directory: {}", e)))?;
    
    IsochroneCalculator::export_as_geoparquet(&all_results, &ch.original_network, output_path)?;
    
    println!("✓ Exported walking network to {}", output_path);
    println!("  Speed used: 5 km/h (walking)");
    let total_records: usize = all_results.iter()
        .map(|(_, results)| results.iter().map(|r| r.reachable_nodes).sum::<usize>())
        .sum();
    println!("  Records: {} reachable nodes", total_records);
    
    // Test some shortest paths between test points
    println!("\n6. Testing shortest paths between test points...");
    
    if test_points.len() >= 2 {
        for i in 0..test_points.len().min(3) {
            for j in (i+1)..test_points.len().min(4) {
                let from = test_points[i];
                let to = test_points[j];
                
                match ch.shortest_path(from, to) {
                    Ok(Some((cost, path))) => {
                        println!("  Path {} → {}: cost {:.2}s ({:.1}min), {} nodes", 
                                from, to, cost, cost/60.0, path.len());
                    },
                    Ok(None) => {
                        println!("  Path {} → {}: No path found", from, to);
                    },
                    Err(e) => {
                        println!("  Path {} → {}: Error - {}", from, to, e);
                    }
                }
            }
        }
    }
    
    println!("\n=== Walking Analysis Complete ===");
    println!("Results exported to:");
    println!("  - data/results/walking_network.parquet (with node coordinates)");
    println!("  - Speed: 5 km/h (walking)");
    println!("  - Contains: longitude, latitude, travel times in seconds/minutes");
    println!("\nReady for conversion to geoparquet format for GIS visualization.");
    
    Ok(())
}