use geo_types::{Point, LineString};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use petgraph::graph::{NodeIndex, EdgeIndex, UnGraph};
use petgraph::Graph;
use crate::{RoutingError, RoutingResult};

/// Node identifier type
pub type NodeId = u64;

/// Edge identifier type
pub type EdgeId = u64;

/// Cost type for routing (in seconds or meters)
pub type Cost = f64;

/// Routing modes supported by the library
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RoutingMode {
    Walking,
    Cycling,
    Car,
    Wheelchair,
}

impl RoutingMode {
    /// Get default speed for the routing mode in km/h
    pub fn default_speed(&self) -> f64 {
        match self {
            RoutingMode::Walking => 5.0,
            RoutingMode::Cycling => 15.0,
            RoutingMode::Car => 50.0,
            RoutingMode::Wheelchair => 4.0,
        }
    }
}

/// Node in the routing network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: NodeId,
    pub location: Point<f64>,
    pub elevation: Option<f64>,
}

impl Node {
    pub fn new(id: NodeId, lon: f64, lat: f64) -> Self {
        Self {
            id,
            location: Point::new(lon, lat),
            elevation: None,
        }
    }

    pub fn with_elevation(mut self, elevation: f64) -> Self {
        self.elevation = Some(elevation);
        self
    }
}

/// Edge in the routing network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    pub id: EdgeId,
    pub source: NodeId,
    pub target: NodeId,
    pub geometry: LineString<f64>,
    pub length: f64,
    pub costs: HashMap<RoutingMode, Cost>,
    pub max_speed: Option<f64>,
    pub oneway: bool,
    pub surface: Option<String>,
    pub highway_type: Option<String>,
}

impl Edge {
    pub fn new(
        id: EdgeId,
        source: NodeId,
        target: NodeId,
        geometry: LineString<f64>,
        length: f64,
    ) -> Self {
        Self {
            id,
            source,
            target,
            geometry,
            length,
            costs: HashMap::new(),
            max_speed: None,
            oneway: false,
            surface: None,
            highway_type: None,
        }
    }

    /// Calculate cost for given routing mode and speed
    pub fn calculate_cost(&mut self, mode: RoutingMode, speed_kmh: Option<f64>) {
        let speed = speed_kmh.unwrap_or(mode.default_speed());
        let time_cost = (self.length / 1000.0) / speed * 3600.0; // Convert to seconds
        self.costs.insert(mode, time_cost);
    }

    /// Get cost for a routing mode
    pub fn get_cost(&self, mode: RoutingMode) -> Option<Cost> {
        self.costs.get(&mode).copied()
    }

    /// Check if edge is accessible for given routing mode
    pub fn is_accessible(&self, mode: RoutingMode) -> bool {
        match mode {
            RoutingMode::Car => {
                // Cars generally need proper roads
                self.highway_type.as_ref().map_or(true, |highway| {
                    !matches!(highway.as_str(), "footway" | "cycleway" | "path" | "steps")
                })
            }
            RoutingMode::Walking => true, // Walking allowed on most edges
            RoutingMode::Cycling => {
                // Cycling restrictions similar to walking but may exclude some highways
                self.highway_type.as_ref().map_or(true, |highway| {
                    !matches!(highway.as_str(), "motorway" | "trunk" | "steps")
                })
            }
            RoutingMode::Wheelchair => {
                // More restrictive than walking
                self.surface.as_ref().map_or(true, |surface| {
                    matches!(surface.as_str(), "paved" | "asphalt" | "concrete")
                }) && self.highway_type.as_ref().map_or(true, |highway| {
                    !matches!(highway.as_str(), "steps" | "path")
                })
            }
        }
    }
}

/// Main network structure for routing
#[derive(Debug, Clone)]
pub struct Network {
    pub graph: UnGraph<Node, EdgeWithCost>,
    pub node_index_map: HashMap<NodeId, NodeIndex>,
    pub edge_index_map: HashMap<EdgeId, EdgeIndex>,
    pub nodes: HashMap<NodeId, Node>,
    pub edges: HashMap<EdgeId, Edge>,
}

/// Edge with cost information for petgraph
#[derive(Debug, Clone)]
pub struct EdgeWithCost {
    pub edge_id: EdgeId,
    pub cost: Cost,
}

impl Network {
    /// Create a new empty network
    pub fn new() -> Self {
        Self {
            graph: Graph::new_undirected(),
            node_index_map: HashMap::new(),
            edge_index_map: HashMap::new(),
            nodes: HashMap::new(),
            edges: HashMap::new(),
        }
    }

    /// Add a node to the network
    pub fn add_node(&mut self, node: Node) -> RoutingResult<()> {
        let node_id = node.id;
        let node_index = self.graph.add_node(node.clone());
        self.node_index_map.insert(node_id, node_index);
        self.nodes.insert(node_id, node);
        Ok(())
    }

    /// Add an edge to the network
    pub fn add_edge(&mut self, mut edge: Edge, mode: RoutingMode) -> RoutingResult<()> {
        // Calculate cost if not already set
        if !edge.costs.contains_key(&mode) {
            edge.calculate_cost(mode, None);
        }

        let cost = edge.get_cost(mode)
            .ok_or_else(|| RoutingError::Network(
                format!("No cost calculated for mode {:?}", mode)
            ))?;

        // Get node indices
        let source_idx = self.node_index_map.get(&edge.source)
            .ok_or_else(|| RoutingError::Network(
                format!("Source node {} not found", edge.source)
            ))?;
        let target_idx = self.node_index_map.get(&edge.target)
            .ok_or_else(|| RoutingError::Network(
                format!("Target node {} not found", edge.target)
            ))?;

        // Add edge to graph
        let edge_with_cost = EdgeWithCost {
            edge_id: edge.id,
            cost,
        };

        let edge_index = self.graph.add_edge(*source_idx, *target_idx, edge_with_cost);
        self.edge_index_map.insert(edge.id, edge_index);
        self.edges.insert(edge.id, edge);

        Ok(())
    }

    /// Get node by ID
    pub fn get_node(&self, node_id: NodeId) -> Option<&Node> {
        self.nodes.get(&node_id)
    }

    /// Get edge by ID
    pub fn get_edge(&self, edge_id: EdgeId) -> Option<&Edge> {
        self.edges.get(&edge_id)
    }

    /// Get node index for petgraph operations
    pub fn get_node_index(&self, node_id: NodeId) -> Option<NodeIndex> {
        self.node_index_map.get(&node_id).copied()
    }

    /// Find nearest node to a given point
    pub fn find_nearest_node(&self, point: &Point<f64>) -> Option<NodeId> {
        let mut min_distance = f64::INFINITY;
        let mut nearest_node = None;

        for (node_id, node) in &self.nodes {
            let distance = self.calculate_distance(point, &node.location);
            if distance < min_distance {
                min_distance = distance;
                nearest_node = Some(*node_id);
            }
        }

        nearest_node
    }

    /// Calculate Haversine distance between two points
    fn calculate_distance(&self, point1: &Point<f64>, point2: &Point<f64>) -> f64 {
        use std::f64::consts::PI;

        let lat1_rad = point1.y() * PI / 180.0;
        let lat2_rad = point2.y() * PI / 180.0;
        let delta_lat = (point2.y() - point1.y()) * PI / 180.0;
        let delta_lon = (point2.x() - point1.x()) * PI / 180.0;

        let a = (delta_lat / 2.0).sin().powi(2)
            + lat1_rad.cos() * lat2_rad.cos() * (delta_lon / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

        6371000.0 * c // Earth radius in meters
    }

    /// Get number of nodes in the network
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Get number of edges in the network
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
    
    /// Get all node IDs in the network
    pub fn get_all_node_ids(&self) -> Vec<NodeId> {
        self.nodes.keys().cloned().collect()
    }

    /// Validate network consistency
    pub fn validate(&self) -> RoutingResult<()> {
        // Check if all edges reference existing nodes
        for (edge_id, edge) in &self.edges {
            if !self.nodes.contains_key(&edge.source) {
                return Err(RoutingError::Network(
                    format!("Edge {} references non-existent source node {}", edge_id, edge.source)
                ));
            }
            if !self.nodes.contains_key(&edge.target) {
                return Err(RoutingError::Network(
                    format!("Edge {} references non-existent target node {}", edge_id, edge.target)
                ));
            }
        }

        // Check graph consistency
        if self.graph.node_count() != self.nodes.len() {
            return Err(RoutingError::Network(
                "Graph node count doesn't match node map".to_string()
            ));
        }

        if self.graph.edge_count() != self.edges.len() {
            return Err(RoutingError::Network(
                "Graph edge count doesn't match edge map".to_string()
            ));
        }

        Ok(())
    }
}