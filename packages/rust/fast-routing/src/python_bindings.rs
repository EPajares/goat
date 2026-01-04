use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::{NetworkLoader, ContractionHierarchy, IsochroneCalculator, IsochroneResult};
use std::collections::HashMap;

/// Python wrapper for the routing network
#[pyclass]
struct PyRoutingNetwork {
    ch: ContractionHierarchy,
}

/// Python wrapper for isochrone results
#[pyclass]
#[derive(Clone)]
struct PyIsochroneResult {
    #[pyo3(get)]
    start_node: u64,
    #[pyo3(get)]
    max_cost: f64,
    #[pyo3(get)]
    reachable_nodes: usize,
    travel_costs: HashMap<u64, f64>,
}

#[pymethods]
impl PyIsochroneResult {
    /// Get all reachable nodes as a list
    fn get_reachable_node_ids(&self) -> Vec<u64> {
        self.travel_costs.keys().cloned().collect()
    }
    
    /// Get node costs as a dictionary
    fn get_node_costs(&self) -> HashMap<u64, f64> {
        self.travel_costs.clone()
    }
    
    /// Get nodes within a specific cost threshold
    fn get_nodes_within_cost(&self, max_cost: f64) -> Vec<u64> {
        self.travel_costs
            .iter()
            .filter(|(_, &cost)| cost <= max_cost)
            .map(|(&node_id, _)| node_id)
            .collect()
    }
    
    /// Get summary statistics
    fn get_stats(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("start_node", self.start_node)?;
            dict.set_item("max_cost", self.max_cost)?;
            dict.set_item("reachable_nodes", self.reachable_nodes)?;
            
            if !self.travel_costs.is_empty() {
                let costs: Vec<f64> = self.travel_costs.values().cloned().collect();
                let min_cost = costs.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let max_cost = costs.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
                let avg_cost = costs.iter().sum::<f64>() / costs.len() as f64;
                
                dict.set_item("min_cost", min_cost)?;
                dict.set_item("max_cost_actual", max_cost)?;
                dict.set_item("avg_cost", avg_cost)?;
            }
            
            Ok(dict.into())
        })
    }
}

#[pymethods]
impl PyRoutingNetwork {
    #[new]
    fn new(network_path: &str) -> PyResult<Self> {
        let network = NetworkLoader::load_from_parquet(network_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        
        let ch = ContractionHierarchy::new(network)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(PyRoutingNetwork { ch })
    }
    
    /// Get network statistics
    fn get_network_info(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("node_count", self.ch.original_network.node_count())?;
            dict.set_item("edge_count", self.ch.original_network.edge_count())?;
            Ok(dict.into())
        })
    }
    
    /// Get all node IDs in the network
    fn get_all_node_ids(&self) -> Vec<u64> {
        self.ch.original_network.get_all_node_ids()
    }
    
    /// Calculate isochrone from a starting point
    fn calculate_isochrone(&self, start_node: u64, max_cost: f64) -> PyResult<PyIsochroneResult> {
        match IsochroneCalculator::calculate(&self.ch, start_node, max_cost) {
            Ok(result) => Ok(convert_isochrone_result(result, start_node, max_cost)),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
        }
    }
    
    /// Calculate multiple isochrones from different starting points
    fn calculate_multiple_isochrones(&self, start_nodes: Vec<u64>, max_cost: f64) -> PyResult<Vec<PyIsochroneResult>> {
        let mut results = Vec::new();
        
        for &start_node in &start_nodes {
            match IsochroneCalculator::calculate(&self.ch, start_node, max_cost) {
                Ok(result) => results.push(convert_isochrone_result(result, start_node, max_cost)),
                Err(e) => {
                    eprintln!("Warning: Failed to calculate isochrone for node {}: {}", start_node, e);
                    continue;
                }
            }
        }
        
        Ok(results)
    }
    
    /// Calculate isochrones with multiple time thresholds
    fn calculate_isochrone_multiple_times(&self, start_node: u64, time_thresholds: Vec<f64>) -> PyResult<Vec<PyIsochroneResult>> {
        let mut results = Vec::new();
        
        for &max_cost in &time_thresholds {
            match IsochroneCalculator::calculate(&self.ch, start_node, max_cost) {
                Ok(result) => results.push(convert_isochrone_result(result, start_node, max_cost)),
                Err(e) => {
                    eprintln!("Warning: Failed to calculate isochrone for time {}: {}", max_cost, e);
                    continue;
                }
            }
        }
        
        Ok(results)
    }
    
    /// Batch calculate isochrones for multiple start points and time thresholds
    fn calculate_batch_isochrones(&self, start_nodes: Vec<u64>, time_thresholds: Vec<f64>) -> PyResult<Vec<PyIsochroneResult>> {
        let mut results = Vec::new();
        
        for &start_node in &start_nodes {
            for &max_cost in &time_thresholds {
                match IsochroneCalculator::calculate(&self.ch, start_node, max_cost) {
                    Ok(result) => results.push(convert_isochrone_result(result, start_node, max_cost)),
                    Err(e) => {
                        eprintln!("Warning: Failed to calculate isochrone for node {} at time {}: {}", start_node, max_cost, e);
                        continue;
                    }
                }
            }
        }
        
        Ok(results)
    }
}

/// Convert Rust IsochroneResult to Python wrapper
fn convert_isochrone_result(result: IsochroneResult, start_node: u64, max_cost: f64) -> PyIsochroneResult {
    PyIsochroneResult {
        start_node,
        max_cost,
        reachable_nodes: result.reachable_nodes,
        travel_costs: result.travel_costs,
    }
}

/// Load a routing network from parquet file
#[pyfunction]
fn load_network(network_path: &str) -> PyResult<PyRoutingNetwork> {
    PyRoutingNetwork::new(network_path)
}

/// Get random sample of node IDs from the network
#[pyfunction]
fn get_random_nodes(network: &PyRoutingNetwork, sample_size: usize) -> Vec<u64> {
    use rand::prelude::*;
    let all_nodes = network.get_all_node_ids();
    let mut rng = thread_rng();
    
    if sample_size >= all_nodes.len() {
        all_nodes
    } else {
        all_nodes.choose_multiple(&mut rng, sample_size).cloned().collect()
    }
}

/// Python module definition
#[pymodule]
fn fast_routing_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyRoutingNetwork>()?;
    m.add_class::<PyIsochroneResult>()?;
    m.add_function(wrap_pyfunction!(load_network, m)?)?;
    m.add_function(wrap_pyfunction!(get_random_nodes, m)?)?;
    
    // Add module metadata
    m.add("__version__", "0.1.0")?;
    m.add("__doc__", "Fast routing library with contraction hierarchies for Python")?;
    
    Ok(())
}