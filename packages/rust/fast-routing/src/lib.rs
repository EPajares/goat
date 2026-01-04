//! Fast Routing Library
//!
//! A high-performance routing library built with Rust, featuring:
//! - Contraction Hierarchies for ultra-fast shortest path queries
//! - Isochrone/catchment area computation
//! - Real-world network data loading from Parquet files

pub mod network;
pub mod contraction;
pub mod isochrone;
pub mod utils;
pub mod dummy_network;
pub mod data_loader;
pub mod error;

// Python bindings module (conditional compilation)
#[cfg(feature = "python")]
pub mod python_bindings;

pub use error::RoutingError;
pub use network::{Network, Node, Edge, RoutingMode};
pub use contraction::ContractionHierarchy;
pub use isochrone::{IsochroneCalculator, IsochroneResult};
pub use dummy_network::DummyNetworkGenerator;
pub use data_loader::NetworkLoader;

/// Result type for the routing library
pub type RoutingResult<T> = Result<T, RoutingError>;