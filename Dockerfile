# Multi-stage build for optimized image size and caching

# Stage 1: UI Builder
FROM oven/bun:1 AS ui_builder

ARG PUBLIC_WS_URL=127.0.0.1:5174/ws

WORKDIR /app

# Copy only UI-related files for better caching
COPY ui/package.json ui/bun.lock* ./ui/
WORKDIR /app/ui

# Install UI dependencies (cached layer)
RUN bun install --frozen-lockfile

# Copy UI source files (we're already in /app/ui, so copy ui/ to current directory)
COPY ui/ .

# Build UI
RUN echo "PUBLIC_WS_URL=${PUBLIC_WS_URL}" >.env && \
    echo "PUBLIC_DESKTOP_MODE=false" >>.env && \
    bun run build

# Stage 2: Python Dependencies Builder with uv
FROM python:3.12-slim AS deps

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

# Install dependencies using uv sync (proper way to install from pyproject.toml)
# First sync without the project to cache dependencies
# Use --frozen if lock file might not be up to date, --locked if it is
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --locked --no-install-project || uv sync --frozen --no-install-project; \
    else \
        uv sync --no-install-project; \
    fi

# Copy the project into the image
COPY . /app

# Sync the project with test dependencies
# Use --frozen to skip lockfile validation if it's out of date
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra test || uv sync --extra test

# Stage 3: Test Dependencies Stage (for running tests in container)
FROM deps AS test-deps

WORKDIR /app

# Application code is already copied in deps stage
# Just ensure tests and save files are available
# (they should already be there from the COPY . /app in deps stage)

# Set up environment to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command runs tests, but can be overridden
CMD ["pytest", "tests/", "-v", "--tb=short"]

# Stage 4: Final Runtime Image
FROM python:3.12-slim

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python virtual environment from deps stage
# uv sync creates a .venv directory with all dependencies
COPY --from=deps /app/.venv /app/.venv

# Set up environment to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY psp.py .
COPY palworld_save_pal ./palworld_save_pal
COPY data ./data

# Copy UI build artifacts from ui_builder stage
COPY --from=ui_builder /app/ui/build ./ui

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5174

# Run application
CMD ["python", "psp.py"]
