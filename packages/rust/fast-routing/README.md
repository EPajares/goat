# Fast Routing

High-performance routing library with contraction hierarchies for real-time isochrone calculations.

## Features

- **Fast isochrone calculations** using contraction hierarchies
- **Python bindings** for easy integration
- **Batch processing** for multiple starting points
- **Real-time performance** suitable for web applications

## Installation

```bash
# Build Python bindings
./setup_python.sh
```

## Usage

```python
import fast_routing_py as routing

# Load network
network = routing.load_network("data/network.parquet")

# Calculate isochrone
result = network.calculate_isochrone(start_node=12345, max_cost=600.0)
print(f"Reachable nodes: {result.reachable_nodes}")
```

## Testing

```bash
# Run Python tests
uv run pytest tests/python/ -v

# Run examples
uv run python examples/python/basic_usage.py
```