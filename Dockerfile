# syntax=docker/dockerfile:1

# ==============================================================================
# Stage 1: Build & Dependency Resolution Stage (builder)
# Compiles dependencies and wheel artifacts in an isolated environment.
# Intermediate build tools (gcc, build-essential, etc.) are discarded afterwards.
# ==============================================================================
FROM python:3.11-slim-bookworm AS builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies required for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment dedicated to application dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy dependency definition and project packaging manifests
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install application and production dependencies into virtual environment
RUN pip install --no-cache-dir .

# Purge bytecode cache, build artifacts, and test files from virtualenv
RUN find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true


# ==============================================================================
# Stage 2: Minimal Production Runtime Stage (runner)
# Contains ONLY the compiled artifacts, minimal runtime shared libraries,
# and runs under a non-root user for strict security compliance.
# ==============================================================================
FROM python:3.11-slim-bookworm AS runner

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src:${PYTHONPATH}" \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install minimal runtime libraries (ca-certificates for TLS, curl for health checks, libpq5 for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system group and user
RUN groupadd --system --gid 10001 coachflow && \
    useradd --system --uid 10001 --gid coachflow --no-create-home --shell /usr/sbin/nologin coachflow

# Copy isolated virtual environment containing installed application & dependencies from builder
COPY --from=builder --chown=coachflow:coachflow /opt/venv /opt/venv

# Copy application source code with non-root ownership
COPY --chown=coachflow:coachflow src/ /app/src/

# Switch to unprivileged non-root user
USER coachflow

# Expose standard FastAPI / Uvicorn application port
EXPOSE 8000

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint
CMD ["uvicorn", "coach_flow.main:app", "--host", "0.0.0.0", "--port", "8000"]
