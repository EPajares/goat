use fast_routing::{NetworkLoader, ContractionHierarchy, RoutingResult};
use std::time::Instant;

fn main() -> RoutingResult<()> {
    env_logger::init();
    
    println!("=== Plan4Better Munich Network Loading Benchmark ===");
    
    let network_path = "data/network.parquet";
    
    // Benchmark network loading multiple times
    println!("1. Network Loading Performance Test");
    println!("   Running 5 iterations to measure consistency...");
    
    let mut load_times = Vec::new();
    let mut node_counts = Vec::new();
    let mut edge_counts = Vec::new();
    
    for i in 1..=5 {
        println!("\n   Iteration {}:", i);
        
        // Network loading
        let start_time = Instant::now();
        let network = NetworkLoader::load_from_parquet(network_path)?;
        let load_time = start_time.elapsed();
        
        let nodes = network.node_count();
        let edges = network.edge_count();
        
        println!("     Loaded {} nodes, {} edges in {:.3}s", nodes, edges, load_time.as_secs_f64());
        
        load_times.push(load_time.as_secs_f64());
        node_counts.push(nodes);
        edge_counts.push(edges);
        
        // Memory cleanup between iterations
        drop(network);
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
    
    // Calculate statistics
    let avg_load_time = load_times.iter().sum::<f64>() / load_times.len() as f64;
    let min_load_time = load_times.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let max_load_time = load_times.iter().fold(0.0f64, |a, &b| a.max(b));
    let std_dev = (load_times.iter().map(|x| (x - avg_load_time).powi(2)).sum::<f64>() / load_times.len() as f64).sqrt();
    
    println!("\n=== Loading Performance Statistics ===");
    println!("Network: Plan4Better Munich");
    println!("Nodes: {}", node_counts[0]);
    println!("Edges: {}", edge_counts[0]);
    println!("");
    println!("Loading Times:");
    println!("  Average: {:.3}s", avg_load_time);
    println!("  Min:     {:.3}s", min_load_time);
    println!("  Max:     {:.3}s", max_load_time);
    println!("  Std Dev: {:.3}s", std_dev);
    println!("");
    
    // Performance metrics
    let edges_per_sec = edge_counts[0] as f64 / avg_load_time;
    let nodes_per_sec = node_counts[0] as f64 / avg_load_time;
    
    println!("Processing Rate:");
    println!("  {:.0} edges/second", edges_per_sec);
    println!("  {:.0} nodes/second", nodes_per_sec);
    println!("");
    
    // Benchmark contraction hierarchy building
    println!("2. Contraction Hierarchy Building Benchmark");
    
    let network = NetworkLoader::load_from_parquet(network_path)?;
    let mut ch_times = Vec::new();
    
    for i in 1..=3 {
        println!("   Building CH iteration {}...", i);
        let start_time = Instant::now();
        let _ch = ContractionHierarchy::new(network.clone())?;
        let ch_time = start_time.elapsed();
        
        println!("     Built in {:.3}s", ch_time.as_secs_f64());
        ch_times.push(ch_time.as_secs_f64());
    }
    
    let avg_ch_time = ch_times.iter().sum::<f64>() / ch_times.len() as f64;
    let min_ch_time = ch_times.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let max_ch_time = ch_times.iter().fold(0.0f64, |a, &b| a.max(b));
    
    println!("\nContraction Hierarchy Statistics:");
    println!("  Average: {:.3}s", avg_ch_time);
    println!("  Min:     {:.3}s", min_ch_time);
    println!("  Max:     {:.3}s", max_ch_time);
    
    // Total pipeline time
    let total_time = avg_load_time + avg_ch_time;
    
    println!("\n=== Complete Pipeline Performance ===");
    println!("Network Loading:  {:.3}s ({:.1}%)", avg_load_time, (avg_load_time / total_time) * 100.0);
    println!("Hierarchy Build:  {:.3}s ({:.1}%)", avg_ch_time, (avg_ch_time / total_time) * 100.0);
    println!("Total Pipeline:   {:.3}s", total_time);
    println!("");
    
    // Compare with original network size
    println!("=== Network Scale Comparison ===");
    println!("Previous OSM network: ~101k nodes, ~131k edges");
    println!("Current P4B network:  {}k nodes, {}k edges", node_counts[0] / 1000, edge_counts[0] / 1000);
    println!("Scale increase: {:.1}x nodes, {:.1}x edges", 
             node_counts[0] as f64 / 101_000.0, 
             edge_counts[0] as f64 / 131_000.0);
    
    // Scalability analysis
    println!("\n=== Scalability Analysis ===");
    println!("Loading rate: {:.0} edges/sec", edges_per_sec);
    println!("For 1M edges: ~{:.1}s estimated", 1_000_000.0 / edges_per_sec);
    println!("For 10M edges: ~{:.1}s estimated", 10_000_000.0 / edges_per_sec);
    
    println!("\n✓ Network loading benchmark complete!");
    println!("Ready for production deployment with Plan4Better network.");
    
    Ok(())
}