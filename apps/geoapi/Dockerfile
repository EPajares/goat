# ==== STAGE 1: General debian environment ====
FROM debian:bookworm-slim AS linux-base

LABEL org.opencontainers.image.source=https://github.com/plan4better/goat
LABEL org.opencontainers.image.description="Goat GeoAPI"
LABEL org.opencontainers.image.licenses="GPL-3.0"

ARG PYTHON_VERSION=3.11


ENV LC_CTYPE=C.utf8 \
    UV_PROJECT_ENVIRONMENT="/venv" \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR="/python" \
    UV_PYTHON=python$PYTHON_VERSION

ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

RUN apt-get update
RUN apt-get upgrade -y

# Install general required dependencies
RUN apt-get install --no-install-recommends -y tzdata

# ==== STAGE 2: Build tippecanoe ====
FROM linux-base AS tippecanoe-builder

ARG TIPPECANOE_VERSION=2.79.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libsqlite3-dev \
    zlib1g-dev \
    && curl -fsSL https://github.com/felt/tippecanoe/archive/refs/tags/${TIPPECANOE_VERSION}.tar.gz -o /tmp/tippecanoe.tar.gz \
    && tar -xzf /tmp/tippecanoe.tar.gz -C /tmp \
    && cd /tmp/tippecanoe-${TIPPECANOE_VERSION} \
    && make -j$(nproc) \
    && make install \
    && rm -rf /tmp/tippecanoe*

# ===== STAGE 3: Python environment ====
FROM linux-base AS python-base
# Install debian dependencies including GDAL for building Python bindings
RUN apt-get update && apt-get install --no-install-recommends -y build-essential gettext libgdal-dev
# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /usr/local/bin/uv

# Create virtual environment and install dependencies
COPY apps/geoapi /app/apps/geoapi
COPY packages/python/goatlib /app/packages/python/goatlib
COPY pyproject.toml uv.lock /app/

WORKDIR /app

RUN uv sync --all-extras --frozen --no-dev --no-editable --package=geoapi

# ==== STAGE 4: Webapp environment ====
FROM linux-base AS webapp

# Install GDAL runtime library needed by Python bindings
# Install zlib runtime needed by tippecanoe
RUN apt-get update && apt-get install --no-install-recommends -y libgdal32 zlib1g && rm -rf /var/lib/apt/lists/*

# Copy tippecanoe binaries (tippecanoe-overzoom for variable-depth tile pyramids)
COPY --from=tippecanoe-builder /usr/local/bin/tippecanoe-overzoom /usr/local/bin/

RUN useradd -m appuser

# Copy python, virtual env and static assets
COPY --from=python-base $UV_PYTHON_INSTALL_DIR $UV_PYTHON_INSTALL_DIR
COPY --from=python-base $UV_PROJECT_ENVIRONMENT $UV_PROJECT_ENVIRONMENT
COPY --from=python-base /app /app

RUN chown -R appuser:appuser /app $UV_PROJECT_ENVIRONMENT $UV_PYTHON_INSTALL_DIR
USER appuser

WORKDIR /app

EXPOSE 8000

CMD ["fastapi", "run", "apps/geoapi/src/geoapi/main.py"]

