use fast_routing::{NetworkLoader, ContractionHierarchy, IsochroneCalculator, RoutingResult};
use std::time::{Duration, Instant};
use rand::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;
use sysinfo::{System, Pid};

struct ResourceMonitor {
    measurements: Arc<Mutex<Vec<ResourceMeasurement>>>,
}

#[derive(Debug, Clone)]
struct ResourceMeasurement {
    timestamp: f64,
    memory_mb: f64,
    cpu_percent: f64,
    system_memory_used_percent: f64,
}

impl ResourceMonitor {
    fn new() -> Self {
        Self {
            measurements: Arc::new(Mutex::new(Vec::new())),
        }
    }

    fn start_monitoring(&mut self) -> Arc<Mutex<Vec<ResourceMeasurement>>> {
        let measurements = Arc::clone(&self.measurements);
        let pid = std::process::id();
        
        thread::spawn(move || {
            let mut system = System::new_all();
            let start_time = Instant::now();
            
            loop {
                system.refresh_all();
                
                if let Some(process) = system.process(Pid::from(pid as usize)) {
                    let timestamp = start_time.elapsed().as_secs_f64();
                    let memory_mb = process.memory() as f64 / 1024.0 / 1024.0;
                    let cpu_percent = process.cpu_usage() as f64;
                    let system_memory_used_percent = (system.used_memory() as f64 / system.total_memory() as f64) * 100.0;
                    
                    let measurement = ResourceMeasurement {
                        timestamp,
                        memory_mb,
                        cpu_percent,
                        system_memory_used_percent,
                    };
                    
                    if let Ok(mut measurements) = measurements.lock() {
                        measurements.push(measurement);
                    }
                }
                
                thread::sleep(Duration::from_millis(100)); // Sample every 100ms
            }
        });
        
        Arc::clone(&self.measurements)
    }
}

fn print_system_info() {
    let mut system = System::new_all();
    system.refresh_all();
    
    println!("=== System Information ===");
    println!("OS: {} {}", System::name().unwrap_or("Unknown".to_string()), System::os_version().unwrap_or("Unknown".to_string()));
    println!("CPU: {} cores", system.cpus().len());
    if let Some(cpu) = system.cpus().first() {
        println!("CPU Brand: {}", cpu.brand());
    }
    println!("Total Memory: {:.2} GB", system.total_memory() as f64 / 1024.0 / 1024.0 / 1024.0);
    println!("Available Memory: {:.2} GB", system.available_memory() as f64 / 1024.0 / 1024.0 / 1024.0);
    println!();
}

fn print_resource_stats(measurements: &[ResourceMeasurement]) {
    if measurements.is_empty() {
        println!("No resource measurements collected");
        return;
    }
    
    let memory_values: Vec<f64> = measurements.iter().map(|m| m.memory_mb).collect();
    let cpu_values: Vec<f64> = measurements.iter().map(|m| m.cpu_percent).collect();
    let system_memory_values: Vec<f64> = measurements.iter().map(|m| m.system_memory_used_percent).collect();
    
    println!("=== Resource Usage Statistics ===");
    println!("Monitoring duration: {:.2}s ({} samples)", 
        measurements.last().unwrap().timestamp, 
        measurements.len());
    
    println!("\nProcess Memory Usage:");
    println!("  Peak: {:.2} MB", memory_values.iter().fold(0.0f64, |a, &b| a.max(b)));
    println!("  Average: {:.2} MB", memory_values.iter().sum::<f64>() / memory_values.len() as f64);
    println!("  Final: {:.2} MB", memory_values.last().unwrap_or(&0.0));
    
    println!("\nProcess CPU Usage:");
    println!("  Peak: {:.1}%", cpu_values.iter().fold(0.0f64, |a, &b| a.max(b)));
    println!("  Average: {:.1}%", cpu_values.iter().sum::<f64>() / cpu_values.len() as f64);
    
    println!("\nSystem Memory Usage:");
    println!("  Peak: {:.1}%", system_memory_values.iter().fold(0.0f64, |a, &b| a.max(b)));
    println!("  Average: {:.1}%", system_memory_values.iter().sum::<f64>() / system_memory_values.len() as f64);
}

fn export_monitoring_csv(measurements: &[ResourceMeasurement], filename: &str) -> std::io::Result<()> {
    use std::io::Write;
    
    let mut file = std::fs::File::create(filename)?;
    writeln!(file, "timestamp_seconds,process_memory_mb,process_cpu_percent,system_memory_percent")?;
    
    for measurement in measurements {
        writeln!(file, "{:.3},{:.2},{:.2},{:.2}", 
                measurement.timestamp,
                measurement.memory_mb,
                measurement.cpu_percent,
                measurement.system_memory_used_percent)?;
    }
    
    println!("Exported monitoring data to {}", filename);
    Ok(())
}

fn main() -> RoutingResult<()> {
    env_logger::init();
    
    print_system_info();
    
    println!("=== 5k Isochrone Benchmark with Resource Monitoring ===\n");
    
    // Start resource monitoring
    let mut monitor = ResourceMonitor::new();
    let measurements = monitor.start_monitoring();
    
    println!("1. Loading network data...");
    let load_start = Instant::now();
    let network_path = "data/network.parquet";
    let network = NetworkLoader::load_from_parquet(network_path)?;
    let load_time = load_start.elapsed();
    
    println!("Network loaded: {} nodes, {} edges ({:.3}s)", 
             network.node_count(), 
             network.edge_count(),
             load_time.as_secs_f64());
    
    println!("\n2. Building contraction hierarchy...");
    let hierarchy_start = Instant::now();
    let ch = ContractionHierarchy::new(network)?;
    let hierarchy_time = hierarchy_start.elapsed();
    println!("Hierarchy built in {:.3}s", hierarchy_time.as_secs_f64());
    
    println!("\n3. Selecting 5000 random starting points...");
    let mut rng = thread_rng();
    let all_node_ids: Vec<u64> = ch.original_network.get_all_node_ids();
    
    let sample_size = std::cmp::min(5000, all_node_ids.len());
    let test_points: Vec<u64> = all_node_ids.choose_multiple(&mut rng, sample_size)
        .cloned()
        .collect();
    
    println!("Selected {} starting points", test_points.len());
    
    println!("\n4. Computing isochrones...");
    let computation_start = Instant::now();
    
    let time_thresholds = vec![300.0, 600.0, 900.0, 1200.0]; // 5, 10, 15, 20 minutes
    
    let mut all_results = Vec::new();
    let mut total_reachable = 0;
    let mut stats_by_time: HashMap<u32, (Vec<usize>, usize)> = HashMap::new();
    
    for (i, &start_node) in test_points.iter().enumerate() {
        if i % 500 == 0 {
            let elapsed = computation_start.elapsed().as_secs_f64();
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
                    let time_key = max_cost as u32;
                    let reachable_count = result.reachable_nodes;
                    total_reachable += reachable_count;
                    
                    stats_by_time.entry(time_key)
                        .or_insert_with(|| (Vec::new(), 0))
                        .0.push(reachable_count);
                    stats_by_time.get_mut(&time_key).unwrap().1 += reachable_count;
                    
                    point_results.push(result);
                },
                Err(e) => {
                    log::warn!("Error calculating isochrone for node {}: {}", start_node, e);
                }
            }
        }
        
        all_results.push((start_node, point_results));
    }
    
    let computation_time = computation_start.elapsed();
    
    // Stop monitoring and get final measurements
    thread::sleep(Duration::from_millis(200)); // Allow final measurements
    let final_measurements = {
        let measurements_guard = measurements.lock().unwrap();
        measurements_guard.clone()
    };
    
    println!("\n=== Benchmark Results ===");
    println!("Total computation time: {:.2} seconds", computation_time.as_secs_f64());
    println!("Points processed: {}", test_points.len());
    println!("Isochrones calculated: {}", all_results.len() * time_thresholds.len());
    println!("Total reachable nodes: {}", total_reachable);
    
    println!("\nPerformance metrics:");
    println!("  {:.1} starting points per second", test_points.len() as f64 / computation_time.as_secs_f64());
    println!("  {:.1} isochrones per second", (all_results.len() * time_thresholds.len()) as f64 / computation_time.as_secs_f64());
    println!("  {:.2} ms average per isochrone", computation_time.as_millis() as f64 / (all_results.len() * time_thresholds.len()) as f64);
    
    println!("\nResults by time threshold:");
    for &time_limit in &[300, 600, 900, 1200] {
        if let Some((counts, total)) = stats_by_time.get(&time_limit) {
            let avg = if !counts.is_empty() { total / counts.len() } else { 0 };
            let min_val = *counts.iter().min().unwrap_or(&0);
            let max_val = *counts.iter().max().unwrap_or(&0);
            println!(
                "  {}s ({}min): avg {} nodes, range {}-{}, total {}",
                time_limit, time_limit / 60, avg, min_val, max_val, total
            );
        }
    }
    
    // Print resource usage statistics
    println!();
    print_resource_stats(&final_measurements);
    
    // Export monitoring data
    export_monitoring_csv(&final_measurements, "data/results/resource_monitoring_5k.csv")?;
    
    println!("\n=== Benchmark Complete ===");
    println!("Network loading: {:.2} seconds", load_time.as_secs_f64());
    println!("Hierarchy building: {:.2} seconds", hierarchy_time.as_secs_f64());
    println!("Isochrone calculation: {:.2} seconds", computation_time.as_secs_f64());
    println!("Total time: {:.2} seconds", (load_time + hierarchy_time + computation_time).as_secs_f64());
    
    println!("\nOutput files:");
    println!("  - data/results/resource_monitoring_5k.csv (system monitoring data)");
    
    Ok(())
}