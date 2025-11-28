# Fast Routing - Python Bindings

High-performance routing library with Python bindings for real-time isochrone calculations.

## 🗂️ Directory Structure

```
fast-routing/
├── tests/python/           # Python test suite
│   ├── test_bindings.py   # Comprehensive binding tests
│   └── conftest.py        # pytest configuration
├── examples/python/        # Python usage examples
│   ├── basic_usage.py     # Basic functionality demo
│   └── legacy_test.py     # Legacy test (reference)
└── python/                # Python module
    └── __init__.py        # Module initialization
```

## 🚀 Quick Start

### Setup

```bash
# Install and build the Python bindings
./setup_python.sh
```

### Run Tests

```bash
# Run all Python tests
uv run pytest tests/python/ -v

# Run with benchmarks
uv run pytest tests/python/ -v --benchmark-only
```

### Run Examples

```bash
# Basic usage demonstration
uv run python examples/python/basic_usage.py

# Legacy test (comprehensive example)
uv run python examples/python/legacy_test.py
```

## 📊 Usage Example

```python
import fast_routing_py as routing

# Load network
network = routing.load_network("data/network.parquet")

# Calculate 10-minute walking catchment
result = network.calculate_isochrone(start_node=12345, max_cost=600.0)

print(f"Reachable nodes: {result.reachable_nodes}")
print(f"Max travel time: {result.max_cost/60:.1f} minutes")
```

## 🧪 Testing

The test suite includes:

- **Module import tests** - Verify bindings are correctly built
- **Network loading tests** - Test parquet file loading  
- **Isochrone calculation tests** - Single and batch calculations
- **Performance benchmarks** - Speed and memory testing
- **Error handling tests** - Edge cases and error conditions

## 📈 Performance

- **Sub-millisecond** isochrone calculations
- **Batch processing** for multiple start points
- **Memory efficient** large network handling
- **Real-time capable** for interactive applications

## 🔧 Development

To modify the Python bindings:

1. Edit Rust code in `src/python_bindings.rs`
2. Rebuild with `maturin develop --release`
3. Run tests with `pytest tests/python/ -v`

## 📝 Notes

- Requires network data in `data/network.parquet`
- Built with [maturin](https://github.com/PyO3/maturin) and [PyO3](https://github.com/PyO3/pyo3)
- Compatible with Python 3.8+