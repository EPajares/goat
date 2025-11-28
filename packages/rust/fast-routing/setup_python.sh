#!/bin/bash
set -e

echo "🚀 Setting up Fast Routing Python bindings with uv..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required but not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install maturin if not available
if ! command -v maturin &> /dev/null; then
    echo "📦 Installing maturin..."
    uv tool install maturin
fi

# Install optional dependencies for development
echo "📦 Installing optional dependencies..."
uv add pytest pytest-benchmark numpy --dev

# Build the Python extension in development mode
echo "🔨 Building Python extension..."
uv run maturin develop --features python

# Test the installation
echo "✅ Testing installation..."
uv run python -c "import fast_routing_py; print('✓ fast_routing_py imported successfully')"

echo ""
echo "🎉 Setup complete! You can now run tests and examples:"
echo "   # Run comprehensive tests:"
echo "   uv run pytest tests/python/ -v"
echo "   # Run basic usage example:"
echo "   uv run python examples/python/basic_usage.py"
echo "   # Run legacy test (for reference):"
echo "   uv run python examples/python/legacy_test.py"
echo ""
echo "Or use in Python:"
echo "   import fast_routing_py as routing"
echo "   network = routing.load_network('data/network.parquet')"