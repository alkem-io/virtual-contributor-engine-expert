# Stage 1: Build stage - install dependencies using Debian Python for distroless compatibility
FROM debian:bookworm-slim AS builder

# Install Python, pip, git and build essentials in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment using Debian's Python (compatible with distroless)
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Poetry in the virtual environment
RUN pip install --no-cache-dir poetry --break-system-packages

# Configure Poetry to install into the existing venv
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copy only dependency files first (better layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev dependencies)
RUN poetry install --only main --no-root --no-ansi

# Stage 2: Runtime stage - Google distroless Python image
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# Copy virtual environment site-packages from builder
# We copy to dist-packages which is on the default python path in Debian/Distroless
COPY --from=builder /venv/lib/python3.11/site-packages /usr/lib/python3.11/dist-packages

# Copy application code
# We use .dockerignore to exclude unwanted files
COPY --chown=nonroot:nonroot . /app

# Environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/lib/python3.11/dist-packages

# Explicitly define the user (good practice)
USER nonroot

# Run main.py when the container launches
ENTRYPOINT ["python3", "main.py"]
