# GOAT Processes API

OGC API - Processes implementation for GOAT geospatial analysis tools.

## Overview

This service implements [OGC API - Processes - Part 1: Core (OGC 18-062r2)](https://docs.ogc.org/is/18-062r2/18-062r2.html) and provides:

- **Async tool execution** via Windmill (buffer, clip, heatmap, etc.)
- **Sync analytics queries** (feature-count, class-breaks, unique-values, etc.)
- **Job management** (status, results, cancellation)

## Why a Separate Service?

This service was separated from GeoAPI to prevent long-running analysis jobs from blocking tile requests. Benefits include:

- **Independent scaling** - Scale processes workers separately from tile servers
- **Resource isolation** - Heavy analytics don't affect map rendering performance
- **Clear separation of concerns** - OGC Processes vs OGC Features/Tiles

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /processes` | List available processes |
| `GET /processes/{processId}` | Get process description |
| `POST /processes/{processId}/execution` | Execute a process |
| `GET /jobs` | List jobs for authenticated user |
| `GET /jobs/{jobId}` | Get job status |
| `GET /jobs/{jobId}/results` | Get job results |
| `DELETE /jobs/{jobId}` | Cancel/dismiss a job |

## Process Categories

### Sync Analytics (Public Access)
- `feature-count` - Count features in a collection
- `unique-values` - Get unique values for an attribute
- `class-breaks` - Calculate class breaks for styling
- `area-statistics` - Calculate area statistics
- `extent` - Get bounding box extent
- `aggregation-stats` - Group-by aggregation statistics
- `histogram` - Generate histogram for numeric column

### Async Tools (Authentication Required)
- **Geoprocessing**: buffer, clip, intersect, union, dissolve, join, aggregate_points, aggregate_polygons
- **Accessibility**: catchment_area, single_isochrone, heatmap_gravity, heatmap_connectivity
- **Public Transport**: nearby_stations, pt_nearby_stations, trip_count_station, origin_destination
- **Reporting**: print_report

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | GOAT Processes API |
| `KEYCLOAK_BASE_URL` | Keycloak URL for JWT validation | - |
| `KEYCLOAK_REALM` | Keycloak realm | goat |
| `WINDMILL_URL` | Windmill API URL | http://localhost:8000 |
| `WINDMILL_WORKSPACE` | Windmill workspace | goat |
| `WINDMILL_TOKEN` | Windmill API token | - |
| `DUCKLAKE_PATH` | DuckLake database path | - |
| `DUCKLAKE_CATALOG` | DuckLake catalog name | main |
| `TRAVELTIME_MATRICES_DIR` | Path to traveltime matrices | /app/data/traveltime |
| `CORS_ORIGINS` | Allowed CORS origins | ["*"] |

## Development

```bash
# Run locally
cd apps/processes
fastapi dev src/processes/main.py

# Run tests
pytest

# Format code
ruff format .
ruff check --fix .
```

## Docker

```bash
# Build
docker build -t goat-processes -f apps/processes/Dockerfile .

# Run
docker run -p 8000:8000 goat-processes
```

## Architecture

```
processes/
├── config.py           # Settings and configuration
├── main.py            # FastAPI application
├── ducklake.py        # DuckLake database manager
├── dependencies.py    # Layer ID normalization helpers
├── deps/
│   └── auth.py        # JWT authentication dependencies
├── models/
│   └── processes.py   # OGC Processes Pydantic models
├── routers/
│   └── processes.py   # OGC Processes API endpoints
└── services/
    ├── analytics_service.py    # Sync analytics queries
    ├── analytics_registry.py   # Analytics process registry
    ├── tool_registry.py        # Async tool process registry
    └── windmill_client.py      # Windmill API wrapper
```
