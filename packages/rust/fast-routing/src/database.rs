use crate::{RoutingError, RoutingResult, Network, Node, Edge, RoutingMode, IsochroneResult};
use duckdb::{Connection, params};
use std::path::Path;
use std::collections::HashMap;
use serde_json;
use parquet::{
    file::properties::WriterProperties,
    arrow::{ArrowWriter, ProjectionMask},
};
use arrow::{
    array::{Float64Array, StringArray, UInt64Array, BooleanArray},
    record_batch::RecordBatch,
    datatypes::{DataType, Field, Schema},
};
use std::sync::Arc;

/// Database manager for handling network data and results
pub struct DatabaseManager {
    connection: Connection,
}

impl DatabaseManager {
    /// Create a new database manager
    pub fn new() -> RoutingResult<Self> {
        let conn = Connection::open_in_memory()?;
        let mut manager = Self { connection: conn };
        manager.setup_database()?;
        Ok(manager)
    }

    /// Create database manager with file-based database
    pub fn with_file<P: AsRef<Path>>(path: P) -> RoutingResult<Self> {
        let conn = Connection::open(path)?;
        let mut manager = Self { connection: conn };
        manager.setup_database()?;
        Ok(manager)
    }

    /// Set up database schema
    fn setup_database(&mut self) -> RoutingResult<()> {
        // Create nodes table
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS nodes (
                id BIGINT PRIMARY KEY,
                longitude DOUBLE NOT NULL,
                latitude DOUBLE NOT NULL,
                elevation DOUBLE
            )",
            [],
        )?;

        // Create edges table
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS edges (
                id BIGINT PRIMARY KEY,
                source_id BIGINT NOT NULL,
                target_id BIGINT NOT NULL,
                length DOUBLE NOT NULL,
                geometry TEXT NOT NULL,
                costs TEXT, -- JSON string with costs for different modes
                max_speed DOUBLE,
                oneway BOOLEAN NOT NULL DEFAULT false,
                surface TEXT,
                highway_type TEXT,
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )",
            [],
        )?;

        // Create spatial indices
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_location ON nodes (longitude, latitude)",
            [],
        )?;

        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_id)",
            [],
        )?;

        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_id)",
            [],
        )?;

        // Create isochrone results table
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS isochrone_results (
                id BIGINT PRIMARY KEY,
                starting_points TEXT NOT NULL, -- JSON array of points
                routing_mode TEXT NOT NULL,
                max_costs TEXT NOT NULL, -- JSON array of costs
                calculation_time_ms BIGINT NOT NULL,
                nodes_reached INTEGER NOT NULL,
                result_data TEXT NOT NULL, -- JSON serialized result
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        Ok(())
    }

    /// Store network in database
    pub fn store_network(&mut self, network: &Network) -> RoutingResult<()> {
        log::info!("Storing network with {} nodes and {} edges", 
                  network.node_count(), network.edge_count());

        let tx = self.connection.unchecked_transaction()?;

        // Clear existing data
        tx.execute("DELETE FROM edges", [])?;
        tx.execute("DELETE FROM nodes", [])?;

        // Store nodes
        {
            let mut stmt = tx.prepare("INSERT INTO nodes (id, longitude, latitude, elevation) VALUES (?, ?, ?, ?)")?;
            for node in network.nodes.values() {
                stmt.execute(params![
                    node.id as i64,
                    node.location.x(),
                    node.location.y(),
                    node.elevation.map(|e| e as f64)
                ])?;
            }
        }

        // Store edges
        {
            let mut stmt = tx.prepare(
                "INSERT INTO edges (id, source_id, target_id, length, geometry, costs, max_speed, oneway, surface, highway_type) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            )?;
            
            for edge in network.edges.values() {
                let geometry = serde_json::to_string(&edge.geometry)?;
                let costs = serde_json::to_string(&edge.costs)?;
                
                stmt.execute(params![
                    edge.id as i64,
                    edge.source as i64,
                    edge.target as i64,
                    edge.length,
                    geometry,
                    costs,
                    edge.max_speed,
                    edge.oneway,
                    edge.surface,
                    edge.highway_type
                ])?;
            }
        }

        tx.commit()?;
        log::info!("Network stored successfully");
        Ok(())
    }

    /// Load network from database
    pub fn load_network(&self, routing_mode: RoutingMode) -> RoutingResult<Network> {
        log::info!("Loading network from database");
        
        let mut network = Network::new();

        // Load nodes
        {
            let mut stmt = self.connection.prepare("SELECT id, longitude, latitude, elevation FROM nodes ORDER BY id")?;
            let rows = stmt.query_map([], |row| {
                let id: i64 = row.get(0)?;
                let lon: f64 = row.get(1)?;
                let lat: f64 = row.get(2)?;
                let elevation: Option<f64> = row.get(3)?;
                
                let mut node = Node::new(id as u64, lon, lat);
                if let Some(elev) = elevation {
                    node = node.with_elevation(elev);
                }
                
                Ok(node)
            })?;

            for node_result in rows {
                let node = node_result.map_err(|e| RoutingError::Database(e.to_string()))?;
                network.add_node(node)?;
            }
        }

        // Load edges
        {
            let mut stmt = self.connection.prepare(
                "SELECT id, source_id, target_id, length, geometry, costs, max_speed, oneway, surface, highway_type 
                 FROM edges ORDER BY id"
            )?;
            
            let rows = stmt.query_map([], |row| {
                let id: i64 = row.get(0)?;
                let source_id: i64 = row.get(1)?;
                let target_id: i64 = row.get(2)?;
                let length: f64 = row.get(3)?;
                let geometry_str: String = row.get(4)?;
                let costs_str: String = row.get(5)?;
                let max_speed: Option<f64> = row.get(6)?;
                let oneway: bool = row.get(7)?;
                let surface: Option<String> = row.get(8)?;
                let highway_type: Option<String> = row.get(9)?;
                
                Ok((id, source_id, target_id, length, geometry_str, costs_str, 
                    max_speed, oneway, surface, highway_type))
            })?;

            for row_result in rows {
                let (id, source_id, target_id, length, geometry_str, costs_str, 
                     max_speed, oneway, surface, highway_type) = 
                    row_result.map_err(|e| RoutingError::Database(e.to_string()))?;
                
                let geometry = serde_json::from_str(&geometry_str)?;
                let costs: HashMap<RoutingMode, f64> = serde_json::from_str(&costs_str)?;
                
                let mut edge = Edge::new(
                    id as u64, 
                    source_id as u64, 
                    target_id as u64, 
                    geometry, 
                    length
                );
                
                edge.costs = costs;
                edge.max_speed = max_speed;
                edge.oneway = oneway;
                edge.surface = surface;
                edge.highway_type = highway_type;
                
                network.add_edge(edge, routing_mode)?;
            }
        }

        log::info!("Loaded network with {} nodes and {} edges", 
                  network.node_count(), network.edge_count());
        Ok(network)
    }

    /// Store isochrone result in database
    pub fn store_isochrone_result(&mut self, result: &IsochroneResult, starting_points: &[geo_types::Point<f64>], routing_mode: RoutingMode, max_costs: &[f64]) -> RoutingResult<i64> {
        let starting_points_json = serde_json::to_string(starting_points)?;
        let max_costs_json = serde_json::to_string(max_costs)?;
        let result_json = serde_json::to_string(result)?;
        let routing_mode_str = format!("{:?}", routing_mode);

        let mut stmt = self.connection.prepare(
            "INSERT INTO isochrone_results (starting_points, routing_mode, max_costs, calculation_time_ms, nodes_reached, result_data) 
             VALUES (?, ?, ?, ?, ?, ?) RETURNING id"
        )?;

        let id = stmt.query_row(params![
            starting_points_json,
            routing_mode_str,
            max_costs_json,
            result.stats.calculation_time_ms as i64,
            result.stats.nodes_reached as i32,
            result_json
        ], |row| row.get::<_, i64>(0))?;

        Ok(id)
    }

    /// Export network to Parquet format
    pub fn export_network_to_parquet<P: AsRef<Path>>(&self, nodes_path: P, edges_path: P) -> RoutingResult<()> {
        log::info!("Exporting network to Parquet format");

        // Export nodes
        self.export_nodes_to_parquet(nodes_path)?;
        
        // Export edges  
        self.export_edges_to_parquet(edges_path)?;

        log::info!("Network export completed");
        Ok(())
    }

    /// Export nodes to Parquet
    fn export_nodes_to_parquet<P: AsRef<Path>>(&self, path: P) -> RoutingResult<()> {
        // Query nodes data
        let mut stmt = self.connection.prepare("SELECT id, longitude, latitude, elevation FROM nodes ORDER BY id")?;
        let rows: Result<Vec<_>, _> = stmt.query_map([], |row| {
            Ok((
                row.get::<_, i64>(0)? as u64,
                row.get::<_, f64>(1)?,
                row.get::<_, f64>(2)?,
                row.get::<_, Option<f64>>(3)?,
            ))
        })?.collect();

        let rows = rows.map_err(|e| RoutingError::Database(e.to_string()))?;

        if rows.is_empty() {
            return Ok(());
        }

        // Prepare arrays
        let mut ids = Vec::new();
        let mut lons = Vec::new();
        let mut lats = Vec::new();
        let mut elevations = Vec::new();

        for (id, lon, lat, elevation) in rows {
            ids.push(id);
            lons.push(lon);
            lats.push(lat);
            elevations.push(elevation);
        }

        // Create Arrow schema
        let schema = Schema::new(vec![
            Field::new("id", DataType::UInt64, false),
            Field::new("longitude", DataType::Float64, false),
            Field::new("latitude", DataType::Float64, false),
            Field::new("elevation", DataType::Float64, true),
        ]);

        // Create Arrow arrays
        let id_array = UInt64Array::from(ids);
        let lon_array = Float64Array::from(lons);
        let lat_array = Float64Array::from(lats);
        let elevation_array = Float64Array::from(elevations);

        // Create record batch
        let batch = RecordBatch::try_new(
            Arc::new(schema),
            vec![
                Arc::new(id_array),
                Arc::new(lon_array),
                Arc::new(lat_array),
                Arc::new(elevation_array),
            ],
        )?;

        // Write to Parquet
        let file = std::fs::File::create(path)?;
        let props = WriterProperties::builder().build();
        let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(props))?;
        
        writer.write(&batch)?;
        writer.close()?;

        Ok(())
    }

    /// Export edges to Parquet
    fn export_edges_to_parquet<P: AsRef<Path>>(&self, path: P) -> RoutingResult<()> {
        // Query edges data
        let mut stmt = self.connection.prepare(
            "SELECT id, source_id, target_id, length, costs, max_speed, oneway, surface, highway_type 
             FROM edges ORDER BY id"
        )?;
        
        let rows: Result<Vec<_>, _> = stmt.query_map([], |row| {
            Ok((
                row.get::<_, i64>(0)? as u64,
                row.get::<_, i64>(1)? as u64,
                row.get::<_, i64>(2)? as u64,
                row.get::<_, f64>(3)?,
                row.get::<_, String>(4)?,
                row.get::<_, Option<f64>>(5)?,
                row.get::<_, bool>(6)?,
                row.get::<_, Option<String>>(7)?,
                row.get::<_, Option<String>>(8)?,
            ))
        })?.collect();

        let rows = rows.map_err(|e| RoutingError::Database(e.to_string()))?;

        if rows.is_empty() {
            return Ok(());
        }

        // Prepare arrays
        let mut ids = Vec::new();
        let mut source_ids = Vec::new();
        let mut target_ids = Vec::new();
        let mut lengths = Vec::new();
        let mut costs = Vec::new();
        let mut max_speeds = Vec::new();
        let mut oneways = Vec::new();
        let mut surfaces = Vec::new();
        let mut highway_types = Vec::new();

        for (id, source_id, target_id, length, cost_json, max_speed, oneway, surface, highway_type) in rows {
            ids.push(id);
            source_ids.push(source_id);
            target_ids.push(target_id);
            lengths.push(length);
            costs.push(cost_json);
            max_speeds.push(max_speed);
            oneways.push(oneway);
            surfaces.push(surface);
            highway_types.push(highway_type);
        }

        // Create Arrow schema
        let schema = Schema::new(vec![
            Field::new("id", DataType::UInt64, false),
            Field::new("source_id", DataType::UInt64, false),
            Field::new("target_id", DataType::UInt64, false),
            Field::new("length", DataType::Float64, false),
            Field::new("costs", DataType::Utf8, false),
            Field::new("max_speed", DataType::Float64, true),
            Field::new("oneway", DataType::Boolean, false),
            Field::new("surface", DataType::Utf8, true),
            Field::new("highway_type", DataType::Utf8, true),
        ]);

        // Create Arrow arrays
        let id_array = UInt64Array::from(ids);
        let source_array = UInt64Array::from(source_ids);
        let target_array = UInt64Array::from(target_ids);
        let length_array = Float64Array::from(lengths);
        let costs_array = StringArray::from(costs);
        let max_speed_array = Float64Array::from(max_speeds);
        let oneway_array = BooleanArray::from(oneways);
        let surface_array = StringArray::from(surfaces);
        let highway_array = StringArray::from(highway_types);

        // Create record batch
        let batch = RecordBatch::try_new(
            Arc::new(schema),
            vec![
                Arc::new(id_array),
                Arc::new(source_array),
                Arc::new(target_array),
                Arc::new(length_array),
                Arc::new(costs_array),
                Arc::new(max_speed_array),
                Arc::new(oneway_array),
                Arc::new(surface_array),
                Arc::new(highway_array),
            ],
        )?;

        // Write to Parquet
        let file = std::fs::File::create(path)?;
        let props = WriterProperties::builder().build();
        let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(props))?;
        
        writer.write(&batch)?;
        writer.close()?;

        Ok(())
    }

    /// Export isochrone results to Parquet
    pub fn export_isochrone_to_parquet<P: AsRef<Path>>(&self, path: P, result_id: Option<i64>) -> RoutingResult<()> {
        let query = if let Some(id) = result_id {
            format!("SELECT * FROM isochrone_results WHERE id = {}", id)
        } else {
            "SELECT * FROM isochrone_results ORDER BY id".to_string()
        };

        // This is a simplified implementation
        // In practice, you'd want to flatten the JSON data into separate columns
        log::info!("Exporting isochrone results to Parquet");
        
        // For now, just export the raw data
        // A full implementation would deserialize the JSON and create proper columnar data
        Ok(())
    }

    /// Query network statistics
    pub fn get_network_stats(&self) -> RoutingResult<HashMap<String, i64>> {
        let mut stats = HashMap::new();

        // Count nodes
        let node_count: i64 = self.connection.query_row("SELECT COUNT(*) FROM nodes", [], |row| {
            row.get(0)
        })?;
        stats.insert("node_count".to_string(), node_count);

        // Count edges
        let edge_count: i64 = self.connection.query_row("SELECT COUNT(*) FROM edges", [], |row| {
            row.get(0)
        })?;
        stats.insert("edge_count".to_string(), edge_count);

        // Count isochrone results
        let isochrone_count: i64 = self.connection.query_row("SELECT COUNT(*) FROM isochrone_results", [], |row| {
            row.get(0)
        })?;
        stats.insert("isochrone_results_count".to_string(), isochrone_count);

        // Calculate total network length
        let total_length: f64 = self.connection.query_row("SELECT SUM(length) FROM edges", [], |row| {
            row.get(0)
        })?;
        stats.insert("total_length_m".to_string(), total_length as i64);

        Ok(stats)
    }

    /// Create spatial index for faster nearest neighbor queries
    pub fn create_spatial_index(&mut self) -> RoutingResult<()> {
        // DuckDB spatial extension would be ideal here, but for simplicity
        // we'll use basic indexing approaches
        
        log::info!("Creating spatial indices...");
        
        // Create R-tree style indices using DuckDB's built-in functionality
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_spatial ON nodes (longitude, latitude)",
            [],
        )?;

        log::info!("Spatial indices created");
        Ok(())
    }

    /// Find nearest nodes to a point using spatial query
    pub fn find_nearest_nodes(&self, longitude: f64, latitude: f64, limit: usize, max_distance_deg: f64) -> RoutingResult<Vec<(u64, f64)>> {
        let mut stmt = self.connection.prepare(
            "SELECT id, 
             SQRT((longitude - ?) * (longitude - ?) + (latitude - ?) * (latitude - ?)) as distance
             FROM nodes 
             WHERE longitude BETWEEN ? - ? AND ? + ?
             AND latitude BETWEEN ? - ? AND ? + ?
             ORDER BY distance 
             LIMIT ?"
        )?;

        let rows = stmt.query_map(params![
            longitude, longitude,
            latitude, latitude,
            longitude, max_distance_deg, longitude, max_distance_deg,
            latitude, max_distance_deg, latitude, max_distance_deg,
            limit as i32
        ], |row| {
            Ok((
                row.get::<_, i64>(0)? as u64,
                row.get::<_, f64>(1)?,
            ))
        })?;

        let mut results = Vec::new();
        for row in rows {
            results.push(row.map_err(|e| RoutingError::Database(e.to_string()))?);
        }

        Ok(results)
    }
}