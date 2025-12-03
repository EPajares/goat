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

RUN apt-get update
RUN apt-get upgrade -y

# Install general required dependencies
RUN apt-get install --no-install-recommends -y tzdata

# ===== STAGE 2: Runtime dependencies ====
FROM linux-base AS runtime-deps

RUN apt-get update && apt-get install --no-install-recommends -y build-essential gettext wget clang
# Install Qgis, gdal and pymgl
RUN apt-get install -y gdal-bin libgdal-dev
RUN wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg
RUN apt-get install -y qgis python3-qgis
RUN mkdir -p /etc/pki/tls/certs && \
    ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
RUN apt-get -y install xvfb

# ==== STAGE 3: Python environment ====
FROM runtime-deps AS python-base
# Install debian dependencies
RUN apt-get update && apt-get install --no-install-recommends -y build-essential gettext
# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /usr/local/bin/uv
# Create virtual environment and install dependencies
COPY apps/core /app/apps/core
COPY pyproject.toml uv.lock /app/
WORKDIR /app
ENV UV_PYTHON_PREFERENCE=only-managed
# Install project dependencies
RUN uv sync --all-extras --frozen --no-dev --no-editable --package=core

# ==== STAGE 4: Webapp environment ====
FROM runtime-deps AS webapp

# Clean-up
RUN apt-get update -y \
    && apt-get remove -y --purge build-essential wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=:0 \
    XDG_RUNTIME_DIR=/tmp \
    LIBGL_ALWAYS_SOFTWARE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONMALLOC=malloc \
    # This is needed for QGIS.
    PYTHONPATH=".:/usr/lib/python3/dist-packages"

# Copy python, virtual env and static assets
COPY --from=python-base $UV_PYTHON_INSTALL_DIR $UV_PYTHON_INSTALL_DIR
COPY --from=python-base $UV_PROJECT_ENVIRONMENT $UV_PROJECT_ENVIRONMENT
COPY --from=python-base /app /app

RUN useradd -m appuser
RUN chown -R appuser:appuser /app /tmp $UV_PROJECT_ENVIRONMENT $UV_PYTHON_INSTALL_DIR
USER appuser

WORKDIR /app

EXPOSE 8000

CMD ["bash", "-c", "Xvfb ${DISPLAY} -screen 0 '1024x768x24' -ac +extension GLX +render -noreset -nolisten tcp -nolisten unix & exec fastapi run apps/core/src/core/main.py"]

