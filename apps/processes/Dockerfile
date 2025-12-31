# ==== STAGE 1: Build stage ====
FROM motiadev/motia:latest AS builder

LABEL org.opencontainers.image.source=https://github.com/plan4better/goat
LABEL org.opencontainers.image.description="Goat OGC API Processes (Motia)"
LABEL org.opencontainers.image.licenses="GPL-3.0"

# Keep same structure as devcontainer for consistent paths
WORKDIR /app/apps/processes

# Copy the processes application first
COPY apps/processes/ ./

# Copy goatlib (local workspace dependency) - same path as devcontainer
COPY packages/python/goatlib /app/packages/python/goatlib

# Install Node.js production dependencies (skip postinstall since we'll set up Python ourselves)
RUN npm install --omit=dev --ignore-scripts

# Create a proper venv like devcontainer uses
RUN python3 -m venv /app/.venv

# Install all Python dependencies into the venv
RUN /app/.venv/bin/pip install --upgrade pip && \
    /app/.venv/bin/pip install -r requirements.txt && \
    /app/.venv/bin/pip install /app/packages/python/goatlib

# Install Playwright browser
RUN /app/.venv/bin/playwright install chromium --with-deps

# ==== STAGE 2: Production stage ====
FROM motiadev/motia:latest AS production

# Keep same structure as devcontainer
WORKDIR /app/apps/processes

# Set up venv in PATH (same as devcontainer)
ENV PATH="/app/.venv/bin:$PATH"

# Copy built application from builder stage
COPY --from=builder /app /app
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the Motia server port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Start Motia in production mode
CMD ["npm", "run", "start"]
