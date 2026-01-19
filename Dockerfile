# Multi-stage build for optimized image size and caching

# Stage 1: UI Builder
FROM oven/bun:1 AS ui_builder

ARG PUBLIC_WS_URL=127.0.0.1:5174/ws

WORKDIR /app

# Copy package files first for better layer caching
# This allows bun install to be cached when only source code or data changes
COPY ui/package.json ui/bun.lock* ./ui/

WORKDIR /app/ui

# Install dependencies (cached layer - only rebuilds if package.json or bun.lock changes)
# Use cache mount to speed up bun install across builds
# Bun stores its cache in /root/.bun directory
RUN --mount=type=cache,target=/root/.bun \
    bun install --frozen-lockfile

# Copy data directory after install to avoid invalidating bun install cache
# The ui/project.inlang/settings.json references "../data/json/ui/{locale}.json"
WORKDIR /app
COPY data/ ./data/

# Copy remaining UI source files
COPY ui/ ./ui/

WORKDIR /app/ui

# Build UI
RUN echo "PUBLIC_WS_URL=${PUBLIC_WS_URL}" >.env && \
    echo "PUBLIC_DESKTOP_MODE=false" >>.env && \
    bun run build

# Stage 2: Python Dependencies Builder with uv (production dependencies only)
FROM python:3.13-slim AS deps-builder

WORKDIR /app

# Install system dependencies if needed (including build tools for pyooz and PyGObject)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    g++ \
    pkg-config \
    python3-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    libgirepository-2.0-dev \
    gobject-introspection \
    libglib2.0-dev \
    gir1.2-glib-2.0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Copy dependency files first for better layer caching
COPY pyproject.toml .
COPY uv.lock* .

# Install production dependencies only (no test dependencies)
# Try --locked first, then --frozen, then fall back to resolving fresh if lockfile is incompatible
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --locked --no-install-project 2>/dev/null || \
        uv sync --frozen --no-install-project 2>/dev/null || \
        uv sync --no-install-project; \
    else \
        uv sync --no-install-project; \
    fi

# Copy Python application code (but not data to avoid cache invalidation)
# Note: tests directory is NOT copied here - only in test-deps stage
COPY psp.py .
COPY palworld_save_pal ./palworld_save_pal

# Copy data directory separately after install to avoid invalidating uv install cache
COPY data ./data

# Sync the project (production dependencies only, no --extra test)
# Try --frozen first, fall back to resolving fresh if lockfile is incompatible
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen 2>/dev/null || uv sync

# Stage 3: Test Dependencies Stage (for running tests in container)
FROM deps-builder AS test-deps

WORKDIR /app

# Copy tests directory (not included in deps-builder)
COPY tests ./tests

# Install test dependencies on top of production dependencies
# Try --frozen first, fall back to resolving fresh if lockfile is incompatible
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra test 2>/dev/null || uv sync --extra test

# Set up environment to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command runs tests, but can be overridden
CMD ["pytest", "tests/", "-v", "--tb=short"]

# Stage 4: Final Runtime Image (minimal production image)
FROM python:3.13-slim AS runtime

WORKDIR /app

# Install only runtime libraries (not dev packages or build tools)
# PyGObject requires these runtime libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    libgirepository-2.0-0 \
    libgirepository-1.0-1 \
    libglib2.0-0 \
    gir1.2-glib-2.0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python virtual environment from deps-builder stage (production dependencies only)
# uv sync creates a .venv directory with all dependencies
COPY --from=deps-builder /app/.venv /app/.venv

# Set up environment to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code (no tests directory)
COPY psp.py .
COPY palworld_save_pal ./palworld_save_pal
COPY data ./data

# Copy UI build artifacts from ui_builder stage
# SvelteKit outputs to ../ui_build (one directory up from /app/ui)
COPY --from=ui_builder /app/ui_build ./ui

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5174

# Run application
CMD ["python", "psp.py"]
