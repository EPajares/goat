# ==== STAGE 1: General debian environment ====
FROM debian:bookworm-slim AS linux-base

LABEL org.opencontainers.image.source=https://github.com/plan4better/goat
LABEL org.opencontainers.image.description="Goat Core"
LABEL org.opencontainers.image.licenses="GPL-3.0"

ARG PYTHON_VERSION=3.11

ENV LC_CTYPE=C.utf8 \
    UV_PROJECT_ENVIRONMENT="/venv" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR="/python" \
    UV_PYTHON=python$PYTHON_VERSION \
    UV_PYTHON_PREFERENCE=only-managed

ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y tzdata \
    && rm -rf /var/lib/apt/lists/*

# ==== STAGE 2: Python environment ====
FROM linux-base AS python-base

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    gettext \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /usr/local/bin/uv

# Create virtual environment and install dependencies
COPY apps/core /app/apps/core
COPY packages/python/goatlib /app/packages/python/goatlib
COPY pyproject.toml uv.lock /app/
WORKDIR /app

# Install project dependencies
RUN uv sync --all-extras --frozen --no-dev --no-editable --package=core

# Copy GDAL Python bindings from system to venv
RUN cp -r /usr/lib/python3/dist-packages/osgeo* $UV_PROJECT_ENVIRONMENT/lib/python3.11/site-packages/

# ==== STAGE 3: Webapp environment ====
FROM linux-base AS webapp

# Install GDAL runtime libraries
RUN apt-get update && apt-get install --no-install-recommends -y \
    gdal-bin \
    libgdal32 \
    && rm -rf /var/lib/apt/lists/*

# Copy python, virtual env and app
COPY --from=python-base $UV_PYTHON_INSTALL_DIR $UV_PYTHON_INSTALL_DIR
COPY --from=python-base $UV_PROJECT_ENVIRONMENT $UV_PROJECT_ENVIRONMENT
COPY --from=python-base /app /app

RUN useradd -m appuser
RUN chown -R appuser:appuser /app /tmp $UV_PROJECT_ENVIRONMENT $UV_PYTHON_INSTALL_DIR
USER appuser

WORKDIR /app

EXPOSE 8000

CMD ["fastapi", "run", "apps/core/src/core/main.py"]
