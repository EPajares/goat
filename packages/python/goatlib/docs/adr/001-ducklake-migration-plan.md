# ADR-001: Migration from PostgreSQL to DuckLake for User Data Storage

## Status
Proposed

## Date
2024-12-23

## Context

### Current Architecture
Currently, GOAT stores all user data in PostgreSQL/PostGIS using a schema called `user_data`. The architecture is:

1. **Business Logic Tables** (remain in PostgreSQL - `customer` schema):
   - `layer` - Layer metadata, ownership, permissions
   - `project` - Project definitions
   - `folder` - Organizational hierarchy
   - `data_store` - Data store configuration
   - `scenario`, `scenario_feature` - Scenario management
   - User management tables (`accounts` schema)

2. **User Geospatial Data** (currently in PostgreSQL `user_data` schema):
   - `point_{user_id}` - Point geometries per user
   - `line_{user_id}` - Line geometries per user
   - `polygon_{user_id}` - Polygon geometries per user
   - `no_geometry_{user_id}` - Tabular data without geometry
   - `street_network_line_{user_id}` - Street network lines
   - `street_network_point_{user_id}` - Street network nodes

Each table has a standardized schema with:
- 25 integer columns, 25 float columns, 25 text columns
- 5 bigint columns, 10 jsonb columns, 10 boolean columns
- 3 array columns each (int, float, text), 3 timestamp columns
- `layer_id` to reference the layer metadata
- H3 spatial indexing columns for clustering
- Multiple layers share the same table (filtered by `layer_id`)

### Pain Points with Current Approach
1. **Scalability**: Each user gets dedicated tables, leading to table proliferation
2. **Maintenance**: Schema migrations affect all user tables
3. **Performance**: PostGIS for analytical queries on large datasets
4. **Cost**: PostgreSQL storage costs for large geospatial datasets
5. **Flexibility**: Fixed column schema limits attribute flexibility

### Proposed Solution: DuckLake + GeoParquet

**DuckLake** is a transactional data lakehouse framework that:
- Uses PostgreSQL for the **catalog** (metadata, ACID transactions)
- Stores actual data in **Parquet/GeoParquet** files (S3 or local storage)
- Provides DuckDB for fast analytical queries
- Supports concurrent reads/writes with snapshot isolation

## Decision

Migrate user geospatial data from PostgreSQL tables to DuckLake with GeoParquet storage.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GOAT Core API                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐    ┌───────────────────────────────────────────┐  │
│  │     PostgreSQL        │    │              DuckLake                     │  │
│  │                       │    │                                           │  │
│  │  ┌─────────────────┐  │    │  ┌─────────────────┐  ┌───────────────┐  │  │
│  │  │ accounts schema │  │    │  │  DuckLake       │  │ Object Storage│  │  │
│  │  │ - user          │  │    │  │  Catalog (PG)   │  │ (S3/MinIO)    │  │  │
│  │  │ - organization  │  │    │  │  (ducklake.*)   │  │               │  │  │
│  │  │ - team          │  │    │  │                 │  │ org_{org_id}/ │  │  │
│  │  └─────────────────┘  │    │  │  - schema_info  │  │   t_{uuid}/   │  │  │
│  │                       │    │  │  - table_info   │  │     *.parquet │  │  │
│  │  ┌─────────────────┐  │    │  │  - snapshots    │  │               │  │  │
│  │  │ customer schema │  │    │  │  - transactions │  │               │  │  │
│  │  │ - layer ────────┼──┼────┼──┼─► references ───┼──┼───────────────┘  │  │
│  │  │ - project       │  │    │  │    table by     │                     │  │
│  │  │ - folder        │  │    │  │    layer.id     │                     │  │
│  │  │ - data_store    │  │    │  └────────┬────────┘                     │  │
│  │  │ - scenario      │  │    │           │                              │  │
│  │  │ - job           │  │    │           ▼                              │  │
│  │  └─────────────────┘  │    │  ┌────────────────┐                      │  │
│  │                       │    │  │    DuckDB      │ ◄── Query Engine     │  │
│  └──────────────────────┘    │  │  (+ Spatial)   │                      │  │
│                               │  └────────────────┘                      │  │
│                               └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Table Naming Convention
```
DuckLake Table:  lake.org_{organization_id}.t_{layer_id}
                      │         │              │
                      │         │              └── Layer UUID (from customer.layer.id)
                      │         └── Organization UUID (from layer.organization or user.organization)
                      └── DuckLake attached database name
```

### What Stays in PostgreSQL
1. **DuckLake Catalog** - Metadata for DuckLake tables (in a new `ducklake` schema)
2. **Business Logic** (`customer` schema):
   - `layer` - Layer metadata with reference to DuckLake table
   - `project`, `folder`, `data_store`
   - `scenario`, `scenario_feature` (potentially migrate later)
3. **User Management** (`accounts` schema)
4. **Job Queue** and system tables

### What Moves to GeoParquet (via DuckLake)
All user-uploaded geospatial data:
- Feature layers (point, line, polygon)
- Table layers (no geometry)
- Tool result layers (catchment areas, heatmaps, etc.)

### New Data Organization (Simplified)

**Current PostgreSQL approach:**
```
user_data.point_{user_id}     → multiple layers share same table (filter by layer_id)
user_data.line_{user_id}      → fixed schema with 25+ generic columns
user_data.polygon_{user_id}   → requires attribute_mapping for real column names
```

**New DuckLake approach:**
```
{org_id}.{layer_uuid}         → one table per layer (1:1 mapping)
                              → native schema (actual column names)
                              → no attribute_mapping needed
```

**Key simplifications:**
1. **Schema per Organization** - Better multi-tenancy and access control
2. **Table name = Layer UUID** - Direct mapping to `customer.layer.id`
3. **Native columns** - No more `integer_attr1`, `text_attr2` - use actual field names
4. **One table per dataset** - No need to filter by `layer_id`

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. **Set up DuckLake infrastructure**
   ```python
   # apps/core/src/core/storage/ducklake.py
   
   import duckdb
   from typing import Optional
   from uuid import UUID
   
   class DuckLakeManager:
       """Manages DuckLake connections and operations."""
       
       def __init__(
           self,
           postgres_uri: str,
           object_storage_path: str,  # s3://bucket/path or /local/path
           catalog_schema: str = "ducklake"
       ):
           self.postgres_uri = postgres_uri
           self.object_storage_path = object_storage_path
           self.catalog_schema = catalog_schema
           self._con: Optional[duckdb.DuckDBPyConnection] = None
       
       def connect(self) -> duckdb.DuckDBPyConnection:
           """Create DuckDB connection with DuckLake attached."""
           con = duckdb.connect()
           con.install_extension("ducklake")
           con.load_extension("ducklake")
           con.install_extension("spatial")
           con.load_extension("spatial")
           
           # Attach DuckLake catalog
           con.execute(f"""
               ATTACH 'ducklake:{self.postgres_uri}?schema={self.catalog_schema}'
               AS lake (DATA_PATH '{self.object_storage_path}')
           """)
           
           self._con = con
           return con
       
       def create_organization_schema(self, organization_id: UUID) -> None:
           """Create schema for an organization in DuckLake."""
           con = self._con or self.connect()
           schema_name = f"org_{str(organization_id).replace('-', '')}"
           con.execute(f"CREATE SCHEMA IF NOT EXISTS lake.{schema_name}")
       
       def get_table_name(self, organization_id: UUID, layer_id: UUID) -> str:
           """Get fully qualified table name for a layer."""
           schema = f"org_{str(organization_id).replace('-', '')}"
           table = f"t_{str(layer_id).replace('-', '')}"
           return f"lake.{schema}.{table}"
       
       def write_layer(
           self,
           organization_id: UUID,
           layer_id: UUID,
           gdf: "gpd.GeoDataFrame",
       ) -> str:
           """Write a GeoDataFrame to DuckLake as GeoParquet."""
           con = self._con or self.connect()
           
           # Ensure organization schema exists
           self.create_organization_schema(organization_id)
           
           table_name = self.get_table_name(organization_id, layer_id)
           
           # Register the GeoDataFrame and create table
           con.register("temp_gdf", gdf)
           con.execute(f"""
               CREATE OR REPLACE TABLE {table_name} AS 
               SELECT * FROM temp_gdf
           """)
           
           return table_name
       
       def read_layer(
           self,
           organization_id: UUID,
           layer_id: UUID,
           bbox: tuple[float, float, float, float] | None = None,
           limit: int | None = None,
       ) -> "gpd.GeoDataFrame":
           """Read layer data from DuckLake."""
           import geopandas as gpd
           
           con = self._con or self.connect()
           table_name = self.get_table_name(organization_id, layer_id)
           
           query = f"SELECT * FROM {table_name}"
           
           conditions = []
           if bbox:
               xmin, ymin, xmax, ymax = bbox
               conditions.append(
                   f"ST_Intersects(geom, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}))"
               )
           
           if conditions:
               query += " WHERE " + " AND ".join(conditions)
           
           if limit:
               query += f" LIMIT {limit}"
           
           return gpd.read_parquet(con.execute(query).fetch_arrow_table())
       
       def delete_layer(self, organization_id: UUID, layer_id: UUID) -> bool:
           """Delete a layer table from DuckLake."""
           con = self._con or self.connect()
           table_name = self.get_table_name(organization_id, layer_id)
           con.execute(f"DROP TABLE IF EXISTS {table_name}")
           return True
   ```

2. **Add DuckLake configuration to settings**
   ```python
   # apps/core/src/core/core/config.py
   
   class Settings(BaseSettings):
       # ... existing settings ...
       
       # DuckLake settings
       DUCKLAKE_ENABLED: bool = False
       DUCKLAKE_CATALOG_SCHEMA: str = "ducklake"  # Schema in PG for DuckLake catalog
       DUCKLAKE_STORAGE_PATH: str = "/app/data/ducklake"  # or s3://bucket/path
       
       # S3 settings for DuckLake storage (optional)
       DUCKLAKE_S3_ENDPOINT: str | None = None
       DUCKLAKE_S3_ACCESS_KEY: str | None = None
       DUCKLAKE_S3_SECRET_KEY: str | None = None
       DUCKLAKE_S3_BUCKET: str | None = None
   ```

3. **Create DuckLake catalog tables in PostgreSQL**
   ```sql
   -- alembic migration
   CREATE SCHEMA IF NOT EXISTS ducklake;
   
   -- DuckLake will automatically create its catalog tables when attached
   -- but we need to ensure the schema exists and has proper permissions
   ```

### Phase 2: Data Access Layer (Week 3-4)
1. **Create abstract data store interface**
   ```python
   # apps/core/src/core/storage/base.py
   
   from abc import ABC, abstractmethod
   from typing import Any
   from uuid import UUID
   import geopandas as gpd
   
   class DataStoreBase(ABC):
       """Abstract interface for user data storage."""
       
       @abstractmethod
       async def write_features(
           self,
           organization_id: UUID,
           layer_id: UUID,
           features: gpd.GeoDataFrame,
       ) -> int:
           """Write features to storage, returns count written."""
           pass
       
       @abstractmethod
       async def read_features(
           self,
           organization_id: UUID,
           layer_id: UUID,
           bbox: tuple[float, float, float, float] | None = None,
           limit: int | None = None,
       ) -> gpd.GeoDataFrame:
           """Read features from storage."""
           pass
       
       @abstractmethod
       async def delete_layer(self, organization_id: UUID, layer_id: UUID) -> bool:
           """Delete all features for a layer."""
           pass
       
       @abstractmethod
       async def get_layer_info(
           self, organization_id: UUID, layer_id: UUID
       ) -> dict[str, Any]:
           """Get layer statistics (count, bbox, schema, etc.)."""
           pass
   ```

2. **Implement PostgreSQL adapter (current behavior)**
   ```python
   # apps/core/src/core/storage/postgres.py (future - wraps existing logic)
   
   class PostgresDataStore(DataStoreBase):
       """PostgreSQL/PostGIS implementation (current behavior).
       
       This maintains backward compatibility with existing user_data schema.
       Uses attribute_mapping to translate generic columns to real names.
       """
       # Wrap existing crud_layer functionality
   ```

3. **Implement DuckLake adapter**
   ```python
   # apps/core/src/core/storage/ducklake.py
   
   class DuckLakeDataStore(DataStoreBase):
       """DuckLake/GeoParquet implementation.
       
       Key differences from PostgreSQL adapter:
       - One table per layer (not shared tables)
       - Native column names (no attribute_mapping needed)
       - Schema per organization
       """
       
       def __init__(self, settings: Settings):
           self.manager = DuckLakeManager(
               postgres_uri=settings.POSTGRES_DATABASE_URI,
               object_storage_path=settings.DUCKLAKE_STORAGE_PATH,
               catalog_schema=settings.DUCKLAKE_CATALOG_SCHEMA,
           )
       
       async def write_features(
           self,
           organization_id: UUID,
           layer_id: UUID,
           features: gpd.GeoDataFrame,
       ) -> int:
           """Write features to GeoParquet via DuckLake."""
           self.manager.write_layer(organization_id, layer_id, features)
           return len(features)
       
       async def read_features(
           self,
           organization_id: UUID,
           layer_id: UUID,
           bbox: tuple[float, float, float, float] | None = None,
           limit: int | None = None,
       ) -> gpd.GeoDataFrame:
           """Read features from DuckLake."""
           return self.manager.read_layer(organization_id, layer_id, bbox, limit)
       
       async def delete_layer(self, organization_id: UUID, layer_id: UUID) -> bool:
           """Delete layer from DuckLake."""
           return self.manager.delete_layer(organization_id, layer_id)
       
       async def get_layer_info(
           self, organization_id: UUID, layer_id: UUID
       ) -> dict[str, Any]:
           """Get layer metadata from DuckLake catalog."""
           con = self.manager.connect()
           table_name = self.manager.get_table_name(organization_id, layer_id)
           
           # Get count and bbox
           result = con.execute(f"""
               SELECT 
                   COUNT(*) as count,
                   ST_Extent(geom) as bbox,
                   SUM(pg_column_size(t.*)) as size_bytes
               FROM {table_name} t
           """).fetchone()
           
           # Get schema info
           schema = con.execute(f"DESCRIBE {table_name}").fetchall()
           
           return {
               "count": result[0],
               "bbox": result[1],
               "size": result[2],
               "columns": [{"name": col[0], "type": col[1]} for col in schema],
           }
   ```

4. **Create factory for data store selection**
   ```python
   # packages/python/goatlib/src/goatlib/storage/factory.py
   
   def get_data_store(layer: Layer, settings: Settings) -> DataStoreBase:
       """Get appropriate data store based on layer configuration."""
       
       # New layers use DuckLake when enabled
       if settings.DUCKLAKE_ENABLED:
           if layer.data_store and layer.data_store.type == DataStoreType.ducklake:
               return DuckLakeDataStore(settings)
       
       # Legacy layers use PostgreSQL
       return PostgresDataStore(settings)
   ```

### Phase 3: API Integration (Week 5-6)
1. **Update layer CRUD operations**
   ```python
   # apps/core/src/core/crud/crud_layer.py
   
   class CRUDLayer:
       async def import_file(
           self,
           async_session: AsyncSession,
           layer: Layer,
           file_path: Path,
           user: User,
       ) -> Layer:
           """Import file to appropriate storage backend."""
           
           # Determine data store
           data_store = get_data_store(layer, settings)
           
           # Read file with geopandas/duckdb
           gdf = gpd.read_file(file_path)
           
           # Write to storage
           await data_store.write_features(
               user_id=str(user.id),
               layer_id=str(layer.id),
               features=gdf,
           )
           
           # Update layer metadata
           layer.size = await data_store.get_layer_size(user.id, layer.id)
           layer.extent = await data_store.get_layer_extent(user.id, layer.id)
           
           return layer
   ```

2. **Update GeoAPI to support DuckLake sources**
   ```python
   # apps/geoapi/src/geoapi/catalog.py
   
   async def get_collection(collection_id: str) -> Collection:
       """Get collection metadata, supporting both PG and DuckLake."""
       
       if collection_id.startswith("ducklake."):
           # Query DuckLake catalog
           return await get_ducklake_collection(collection_id)
       else:
           # Existing PostgreSQL logic
           return await get_postgres_collection(collection_id)
   ```

3. **Update MVT tile generation**
   ```python
   # Support DuckDB spatial queries for tile generation
   
   async def generate_mvt_ducklake(
       layer_id: str,
       z: int, x: int, y: int
   ) -> bytes:
       """Generate MVT tiles from DuckLake data."""
       
       con = get_ducklake_connection()
       
       # Calculate tile bounds
       bounds = tile_to_bounds(z, x, y)
       
       # Query with spatial filter
       result = con.execute(f"""
           SELECT ST_AsMVT(tile, 'default', 4096, 'geom') as mvt
           FROM (
               SELECT 
                   ST_AsMVTGeom(
                       ST_Transform(geom, 'EPSG:4326', 'EPSG:3857'),
                       ST_MakeEnvelope({bounds}),
                       4096, 64, true
                   ) as geom,
                   * EXCLUDE(geom)
               FROM {table_name}
               WHERE ST_Intersects(
                   geom, 
                   ST_MakeEnvelope({bounds}, 4326)
               )
           ) tile
       """).fetchone()
       
       return result[0] if result else b''
   ```

### Phase 4: Migration Tools (Week 7-8)
1. **Create migration script for existing data**
   ```python
   # scripts/migrate_to_ducklake.py
   
   async def migrate_user_data(
       user_id: str,
       pg_session: AsyncSession,
       ducklake: DuckLakeManager,
   ):
       """Migrate a user's data from PostgreSQL to DuckLake."""
       
       # Get all layers for user
       layers = await get_user_layers(pg_session, user_id)
       
       for layer in layers:
           # Read from PostgreSQL
           gdf = await read_postgres_layer(pg_session, layer)
           
           if gdf.empty:
               continue
           
           # Write to DuckLake
           ducklake.write_layer(
               user_id=user_id,
               layer_id=str(layer.id),
               gdf=gdf,
               geometry_type=layer.feature_layer_geometry_type,
           )
           
           # Update layer metadata to point to DuckLake
           layer.data_store_id = ducklake_data_store.id
           await pg_session.commit()
           
           logger.info(f"Migrated layer {layer.id} ({len(gdf)} features)")
   ```

2. **Add migration endpoint for gradual rollout**
   ```python
   # apps/core/src/core/endpoints/v2/migration.py
   
   @router.post("/migrate-to-ducklake/{layer_id}")
   async def migrate_layer_to_ducklake(
       layer_id: UUID,
       user: User = Depends(get_current_user),
       session: AsyncSession = Depends(get_session),
   ):
       """Migrate a single layer to DuckLake storage."""
       # Implementation
   ```

### Phase 5: Testing & Validation (Week 9-10)
1. **Unit tests for data stores**
2. **Integration tests for CRUD operations**
3. **Performance benchmarks: PostgreSQL vs DuckLake**
4. **Data integrity validation**

### Phase 6: Gradual Rollout (Week 11-12)
1. Enable DuckLake for new layers only (feature flag)
2. Migrate power users first
3. Monitor performance and issues
4. Full rollout

## File Structure

```
apps/core/src/core/
├── storage/                    # NEW - Storage backends
│   ├── __init__.py
│   ├── base.py                 # Abstract DataStoreBase interface
│   └── ducklake.py             # DuckLake/GeoParquet implementation
├── core/
│   └── config.py               # DuckLake settings (DUCKLAKE_*)
├── crud/
│   ├── crud_layer.py           # Update to use storage abstraction
│   └── crud_user.py            # Remove per-user table creation (for new orgs)
├── db/
│   └── models/
│       └── data_store.py       # Add DuckLake type
└── endpoints/v2/
    └── migration.py            # Migration endpoints (future)

scripts/
└── migrate_to_ducklake.py      # Migration tool (future)
```

## DuckLake Data Organization

### PostgreSQL (Catalog + Business Logic)
```sql
-- DuckLake catalog tables (auto-managed by DuckLake)
ducklake.ducklake_schema
ducklake.ducklake_table
ducklake.ducklake_snapshot
ducklake.ducklake_data_file
ducklake.ducklake_transaction

-- Business logic (existing)
customer.layer          -- layer.id references DuckLake table name
customer.organization   -- organization.id is used for schema name
customer.project
customer.folder
```

### GeoParquet Files (Object Storage)
```
{DUCKLAKE_STORAGE_PATH}/
├── org_{org_id_1}/                    # Schema per organization
│   ├── t_{layer_uuid_1}/              # Table per layer (1:1 with customer.layer)
│   │   ├── data_0.parquet             # Partitioned files
│   │   └── data_1.parquet
│   ├── t_{layer_uuid_2}/
│   │   └── data_0.parquet
│   └── ...
├── org_{org_id_2}/
│   └── ...
```

### Example Mapping
```
customer.layer                          DuckLake
─────────────────────────────────────────────────────────────────
id: 550e8400-e29b-41d4-a716-446655440000
user_id: abc-123                   →    lake.org_<org_id>.t_550e8400e29b41d4a716446655440000
organization_id: org-456
name: "My POI Dataset"
feature_layer_geometry_type: point
attribute_mapping: NULL                 (not needed - native columns!)
```

## Benefits

1. **Performance**: DuckDB analytical queries are 10-100x faster for aggregations
2. **Scalability**: Object storage (S3) scales infinitely
3. **Cost**: S3 storage is ~10x cheaper than RDS
4. **Flexibility**: Native schema per dataset (no more `integer_attr1`, `text_attr2`)
5. **Analytics**: Direct integration with data science tools
6. **Interoperability**: GeoParquet is an open standard
7. **Simplicity**: One table per layer, direct UUID mapping, no attribute_mapping
8. **Multi-tenancy**: Organization-based schemas for access control

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Transaction complexity | DuckLake provides ACID guarantees |
| MVT tile performance | Implement caching layer |
| Migration data loss | Run parallel systems, validate checksums |
| DuckLake maturity | Maintain PostgreSQL fallback |

## Alternatives Considered

1. **Pure Parquet on S3** - No ACID guarantees, complex concurrent access
2. **Apache Iceberg** - More complex, less suited for spatial data
3. **Delta Lake** - Spark-centric, less DuckDB integration
4. **Keep PostgreSQL** - Doesn't solve scalability/cost issues

## Decision Outcome

Proceed with DuckLake implementation following the phased approach above.

## References

- [DuckLake Documentation](https://duckdb.org/docs/extensions/ducklake.html)
- [GeoParquet Specification](https://github.com/opengeospatial/geoparquet)
- [DuckDB Spatial Extension](https://duckdb.org/docs/extensions/spatial.html)
- [Current GOAT Data Model](../apps/core/src/core/db/models/)
