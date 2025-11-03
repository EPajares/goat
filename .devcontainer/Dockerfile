FROM python:3.11.12-bookworm

ARG PYTHON_VERSION="3.11.12"
ARG NODE_VERSION="20.15.0"
ARG PNPM_VERSION="9.5.0"

WORKDIR /app

# Update debian
RUN apt-get update
RUN apt-get upgrade -y

# Install general required dependencies
RUN apt-get install --no-install-recommends -y \
    tzdata \
    ca-certificates \
    curl \
    wget \
    git \
    build-essential \
    cmake \
    ccache \
    pkg-config

# GDAL
RUN apt-get install -y gdal-bin libgdal-dev

# QGIS
RUN wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg
RUN apt-get install -y qgis python3-qgis

# PYMGL
ENV DISPLAY=:0 \
    XDG_RUNTIME_DIR=/tmp \
    LIBGL_ALWAYS_SOFTWARE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONMALLOC=malloc \
    BUILD_TEMP_DIR=/tmp/build

RUN mkdir -p /etc/pki/tls/certs && \
    ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt

RUN apt-get -y install xvfb


# UV
ENV PATH="/app/.venv/bin:$PATH" \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python$PYTHON_VERSION \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/uv

# NODE
ENV NVM_DIR=/usr/local/nvm
ENV NODE_VERSION=$NODE_VERSION
RUN mkdir -p $NVM_DIR
RUN curl --silent -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

# CELERY
RUN curl -sSL https://raw.githubusercontent.com/celery/celery/master/extra/generic-init.d/celeryd > /etc/init.d/celeryd && \
    chmod +x /etc/init.d/celeryd

# PNPM
ENV PNPM_VERSION=$PNPM_VERSION
RUN wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash -


# Start Xvfb (virtual display) in the background for pymgl and keep the container running
CMD bash -c "Xvfb ${DISPLAY} -screen 0 '1024x768x24' -ac +extension GLX +render -noreset -nolisten tcp & while true; do sleep 1000; done"


