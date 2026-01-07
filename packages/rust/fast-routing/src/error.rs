use thiserror::Error;

#[derive(Error, Debug)]
pub enum RoutingError {
    #[error("Network error: {0}")]
    Network(String),
    
    #[error("Contraction hierarchy error: {0}")]
    ContractionHierarchy(String),
    
    #[error("Isochrone calculation error: {0}")]
    Isochrone(String),
    
    #[error("Geometry error: {0}")]
    Geometry(String),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}