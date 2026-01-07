use fast_routing::{DummyNetworkGenerator, ContractionHierarchy, IsochroneCalculator, RoutingResult};

fn main() -> RoutingResult<()> {
    env_logger::init();
    
    println!("Creating a larger test network...");
    let network = DummyNetworkGenerator::create_grid(5, 5, 1000.0)?;
    
    println!("Network created with {} nodes and {} edges", 
             network.node_count(), 
             network.edge_count());
    
    println!("Building contraction hierarchy...");
    let ch = ContractionHierarchy::new(network)?;
    
    println!("Calculating isochrone from node 0 within 300 time units...");
    let isochrone_result = IsochroneCalculator::calculate(&ch, 0, 300.0)?;
    
    println!("Isochrone calculation completed!");
    println!("Maximum cost: {:.2}", isochrone_result.max_cost);
    println!("Reachable nodes: {}", isochrone_result.reachable_nodes);
    
    // Test a few shortest paths
    let test_nodes = vec![6, 12, 18, 24];
    for target in test_nodes {
        println!("\nTesting path from node 0 to node {}...", target);
        match ch.shortest_path(0, target)? {
            Some((cost, path)) => {
                println!("  Path found with cost {:.2}: {:?}", cost, path);
            }
            None => {
                println!("  No path found");
            }
        }
    }
    
    println!("\nIsochrone demo completed successfully!");
    
    Ok(())
}