#!/bin/bash
#
# Setup script for PrintReport process dependencies
# Run this script to install Playwright and its Chromium browser
#

set -e

echo "Installing Playwright browser for PrintReport process..."

# Install Playwright Python package dependencies if not already installed
pip install playwright pypdf

# Install Chromium browser with dependencies
playwright install chromium --with-deps

echo "Playwright setup complete!"
echo ""
echo "To verify the installation, run:"
echo "  python -c 'from playwright.async_api import async_playwright; print(\"Playwright OK\")'"
