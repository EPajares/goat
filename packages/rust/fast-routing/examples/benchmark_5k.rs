use fast_routing::{NetworkLoader, ContractionHierarchy, IsochroneCalculator, RoutingResult};
use std::time::Instant;
use rand::prelude::*;

fn main() -> RoutingResult<()> {
    env_logger::init();
    
    println!("=== Walking Catchment Benchmark Test ===");
    println!("Testing performance with 5,000 starting points");
    
    // Load network from Parquet
    println!("\\n1. Loading network from Parquet...");
    let start_time = Instant::now();
    let network_path = "data/network.parquet";
    let network = NetworkLoader::load_from_parquet(network_path)?;
    let load_time = start_time.elapsed();
    
    println!("Network loaded: {} nodes, {} edges ({:.2}s)", 
             network.node_count(), 
             network.edge_count(),
             load_time.as_secs_f64());
    println!("  Speed: 5 km/h (walking mode)");
    
    // Build contraction hierarchy
    println!("\\n2. Building contraction hierarchy...");
    let start_time = Instant::now();
    let ch = ContractionHierarchy::new(network)?;
    let ch_time = start_time.elapsed();
    
    println!("Contraction hierarchy built ({:.2}s)", ch_time.as_secs_f64());
    
    // Generate 5,000 random starting points from available nodes
    println!("\\n3. Generating 5,000 random starting points...");
    let mut rng = thread_rng();
    let all_node_ids: Vec<u64> = ch.original_network.get_all_node_ids();
    
    if all_node_ids.len() < 5000 {
        println!("Network only has {} nodes, using all available", all_node_ids.len());
    }
    
    let sample_size = std::cmp::min(5000, all_node_ids.len());
    let test_points: Vec<u64> = all_node_ids.choose_multiple(&mut rng, sample_size)
        .cloned()
        .collect();
    
    println!("Generated {} random starting points", test_points.len());
    
    // Benchmark different time thresholds
    let time_thresholds = vec![300.0, 600.0, 900.0, 1200.0]; // 5, 10, 15, 20 minutes
    
    println!("\\n4. Running benchmark analysis...");
    println!("   Time thresholds: 5, 10, 15, 20 minutes walking");
    println!("   Starting points: {}", test_points.len());
    
    let mut all_results = Vec::new();
    let mut total_reachable_nodes = 0;
    let benchmark_start = Instant::now();
    
    for (i, &start_node) in test_points.iter().enumerate() {
        if i % 500 == 0 {
            let elapsed = benchmark_start.elapsed().as_secs_f64();
            let rate = if elapsed > 0.0 { i as f64 / elapsed } else { 0.0 };
            let eta = if rate > 0.0 { (test_points.len() - i) as f64 / rate } else { 0.0 };
            
            println!("   Progress: {}/{} ({:.1}%) - {:.1} points per sec - ETA: {:.1}s", 
                    i, test_points.len(), 
                    (i as f64 / test_points.len() as f64) * 100.0,
                    rate, eta);
        }
        
        let mut point_results = Vec::new();
        
        for &max_cost in &time_thresholds {
            match IsochroneCalculator::calculate(&ch, start_node, max_cost) {
                Ok(result) => {
                    total_reachable_nodes += result.reachable_nodes;
                    point_results.push(result);
                },
                Err(e) => {
                    log::warn!("Error calculating isochrone for node {}: {}", start_node, e);
                }
            }
        }
        
        all_results.push((start_node, point_results));
    }
    
    let total_time = benchmark_start.elapsed();
    
    // Calculate performance statistics
    println!("\\n=== Benchmark Results ===");
    println!("Total computation time: {:.2} seconds", total_time.as_secs_f64());
    println!("Points processed: {}", test_points.len());
    println!("Isochrones calculated: {}", test_points.len() * time_thresholds.len());
    println!("Total reachable nodes: {}", total_reachable_nodes);
    
    let points_per_second = test_points.len() as f64 / total_time.as_secs_f64();
    let isochrones_per_second = (test_points.len() * time_thresholds.len()) as f64 / total_time.as_secs_f64();
    
    println!("\\nPerformance metrics:");
    println!("  {:.1} starting points per second", points_per_second);
    println!("  {:.1} isochrones per second", isochrones_per_second);
    println!("  {:.2} ms average per isochrone", 
             (total_time.as_millis() as f64) / (test_points.len() * time_thresholds.len()) as f64);
    
    // Calculate statistics by time threshold
    println!("\\nResults by time threshold:");
    for &threshold in &time_thresholds {
        let threshold_results: Vec<_> = all_results.iter()
            .filter_map(|(_, results)| {
                results.iter().find(|r| r.max_cost == threshold)
            })
            .collect();
        
        let total_nodes: usize = threshold_results.iter().map(|r| r.reachable_nodes).sum();
        let avg_nodes = total_nodes as f64 / threshold_results.len() as f64;
        let max_nodes = threshold_results.iter().map(|r| r.reachable_nodes).max().unwrap_or(0);
        let min_nodes = threshold_results.iter().map(|r| r.reachable_nodes).min().unwrap_or(0);
        
        println!("  {:.0}s ({:.0}min): avg {:.0} nodes, range {}-{}, total {}", 
                threshold, threshold/60.0, avg_nodes, min_nodes, max_nodes, total_nodes);
    }
    
    // Export results
    println!("\\n5. Exporting benchmark results...");
    let output_path = "data/results/benchmark_walking_5k.parquet";
    let export_start = Instant::now();
    
    std::fs::create_dir_all("data/results").map_err(|e| 
        fast_routing::RoutingError::Network(format!("Failed to create results directory: {}", e)))?;
    
    IsochroneCalculator::export_as_geoparquet(&all_results, &ch.original_network, output_path)?;
    let export_time = export_start.elapsed();
    
    println!("Exported benchmark results to {} ({:.2}s)", output_path, export_time.as_secs_f64());
    
    // Final summary
    println!("\\n=== Benchmark Complete ===");
    println!("Network loading: {:.2} seconds", load_time.as_secs_f64());
    println!("Hierarchy building: {:.2} seconds", ch_time.as_secs_f64());
    println!("Isochrone calculation: {:.2} seconds", total_time.as_secs_f64());
    println!("Data export: {:.2} seconds", export_time.as_secs_f64());
    println!("Total time: {:.2} seconds", (load_time + ch_time + total_time + export_time).as_secs_f64());
    
    println!("\\nOutput files:");
    println!("  - {} ({} starting points)", output_path, test_points.len());
    println!("  - Ready for geoparquet conversion");
    
    Ok(())
}