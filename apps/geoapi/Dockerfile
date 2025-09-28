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


# ===== STAGE 2: Python environment ====
FROM linux-base AS python-base
# Install debian dependencies
RUN apt-get install --no-install-recommends -y build-essential gettext
# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

# Create virtual environment and install dependencies
COPY apps/geoapi /app/apps/geoapi
COPY pyproject.toml uv.lock /app/

WORKDIR /app

RUN uv sync --all-extras --frozen --no-dev --no-editable --package=geoapi

# ==== STAGE 3: Webapp environment ====
FROM linux-base AS webapp

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

