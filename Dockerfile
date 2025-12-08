# =============================================================================
# Stage 1: Builder - Install dependencies and export to requirements.txt
# =============================================================================
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bullseye AS builder

# Install git (required for git-based dependencies) and clean up in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry and export plugin
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt and install to a target directory
# This avoids needing Poetry in the final image
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir --target=/app/dependencies -r requirements.txt

# Copy application source code
COPY . .

# =============================================================================
# Stage 2: Runtime - Minimal distroless image
# =============================================================================
FROM gcr.io/distroless/python3-debian11:nonroot

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/dependencies /app/dependencies

# Copy application code
COPY --from=builder /app/*.py /app/
COPY --from=builder /app/prompt_graph /app/prompt_graph/

# Set Python path to include dependencies
ENV PYTHONPATH=/app/dependencies

# Run as non-root user (distroless:nonroot already runs as uid 65532)
# Distroless images use the binary directly, not a shell
ENTRYPOINT ["python", "main.py"]
