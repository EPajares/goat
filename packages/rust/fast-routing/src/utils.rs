use geo_types::Point;

/// Utility functions for the routing library
pub struct Utils;

impl Utils {
    /// Calculate distance between two points in meters using Haversine formula
    pub fn haversine_distance(p1: &Point<f64>, p2: &Point<f64>) -> f64 {
        let r = 6371000.0; // Earth radius in meters
        
        let lat1 = p1.y().to_radians();
        let lat2 = p2.y().to_radians();
        let delta_lat = (p2.y() - p1.y()).to_radians();
        let delta_lon = (p2.x() - p1.x()).to_radians();

        let a = (delta_lat / 2.0).sin().powi(2) +
                lat1.cos() * lat2.cos() * (delta_lon / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

        r * c
    }
}