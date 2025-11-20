#!/usr/bin/env bash
set -e
set -x

# --- Check for local virtual environment (dev) ---
if [ -f "../../venv/bin/activate" ]; then
    echo "Activating local dev virtual environment..."
    source ../../venv/bin/activate
fi

# --- Confirm Python being used ---
echo "Using python: $(which python)"
python --version

# --- Run migrations ---
alembic upgrade head

# --- Load initial data ---
python ./src/core/scripts/initial_data.py