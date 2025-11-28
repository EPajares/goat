use fast_routing::{DummyNetworkGenerator, ContractionHierarchy, IsochroneCalculator};

#[test]
fn test_basic_routing() {
    let network = DummyNetworkGenerator::create_simple().unwrap();
    assert_eq!(network.node_count(), 9);
    assert_eq!(network.edge_count(), 12);
    
    let ch = ContractionHierarchy::new(network).unwrap();
    let stats = ch.stats();
    assert_eq!(stats["nodes"], "9");
    assert_eq!(stats["edges"], "12");
    
    // Test shortest path
    let result = ch.shortest_path(0, 8).unwrap();
    assert!(result.is_some());
    
    let (cost, path) = result.unwrap();
    assert!(cost > 0.0);
    assert!(path.len() >= 2);
    assert_eq!(path[0], 0);
    assert_eq!(path[path.len() - 1], 8);
}

#[test]
fn test_grid_network() {
    let network = DummyNetworkGenerator::create_grid(3, 3, 100.0).unwrap();
    assert_eq!(network.node_count(), 9);
    
    let ch = ContractionHierarchy::new(network).unwrap();
    
    // Test that we can route between corners
    let result = ch.shortest_path(0, 8).unwrap();
    assert!(result.is_some());
}

#[test]
fn test_isochrone() {
    let network = DummyNetworkGenerator::create_simple().unwrap();
    let ch = ContractionHierarchy::new(network).unwrap();
    
    let isochrone = IsochroneCalculator::calculate(&ch, 0, 300.0).unwrap();
    assert_eq!(isochrone.max_cost, 300.0);
    // With 300s limit and ~72s per edge, we should reach all 9 nodes in a 3x3 grid
    assert_eq!(isochrone.reachable_nodes, 9);
}

#[test]
fn test_invalid_routing() {
    let network = DummyNetworkGenerator::create_simple().unwrap();
    let ch = ContractionHierarchy::new(network).unwrap();
    
    // Test routing to non-existent node
    let result = ch.shortest_path(0, 999);
    assert!(result.is_err());
}