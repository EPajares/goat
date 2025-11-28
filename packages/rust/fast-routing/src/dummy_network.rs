use crate::{RoutingResult, network::{Network, Node, Edge, NodeId, RoutingMode}};
use geo_types::{LineString, Coord};

/// Generator for dummy networks for testing
pub struct DummyNetworkGenerator;

impl DummyNetworkGenerator {
    /// Create a simple grid network for testing
    pub fn create_grid(width: usize, height: usize, spacing: f64) -> RoutingResult<Network> {
        let mut network = Network::new();

        // Create grid nodes
        for y in 0..height {
            for x in 0..width {
                let node_id = (y * width + x) as NodeId;
                let lon = x as f64 * spacing;
                let lat = y as f64 * spacing;
                
                let node = Node::new(node_id, lon, lat);
                network.add_node(node)?;
            }
        }

        let mut edge_id = 0;
        
        // Create edges between adjacent nodes
        for y in 0..height {
            for x in 0..width {
                let current_node = (y * width + x) as NodeId;
                
                // Connect to right neighbor
                if x < width - 1 {
                    let right_node = (y * width + (x + 1)) as NodeId;
                    
                    let current_coord = Coord { x: x as f64 * spacing, y: y as f64 * spacing };
                    let right_coord = Coord { x: (x + 1) as f64 * spacing, y: y as f64 * spacing };
                    let geometry = LineString::new(vec![current_coord, right_coord]);
                    
                    let edge = Edge::new(
                        edge_id,
                        current_node,
                        right_node,
                        geometry,
                        spacing,
                    );
                    network.add_edge(edge, RoutingMode::Car)?;
                    edge_id += 1;
                }
                
                // Connect to bottom neighbor
                if y < height - 1 {
                    let bottom_node = ((y + 1) * width + x) as NodeId;
                    
                    let current_coord = Coord { x: x as f64 * spacing, y: y as f64 * spacing };
                    let bottom_coord = Coord { x: x as f64 * spacing, y: (y + 1) as f64 * spacing };
                    let geometry = LineString::new(vec![current_coord, bottom_coord]);
                    
                    let edge = Edge::new(
                        edge_id,
                        current_node,
                        bottom_node,
                        geometry,
                        spacing,
                    );
                    network.add_edge(edge, RoutingMode::Car)?;
                    edge_id += 1;
                }
            }
        }

        Ok(network)
    }

    /// Create a simple test network
    pub fn create_simple() -> RoutingResult<Network> {
        Self::create_grid(3, 3, 1000.0) // 3x3 grid with 1km spacing
    }
}