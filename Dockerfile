# Stage 1: Build stage - Debian Python for distroless compatibility
FROM debian:bookworm-slim AS builder

# Install Python, pip, venv, and git (required for git-based Poetry deps)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a venv whose interpreter path matches distroless (/usr/bin/python3.11)
RUN python3 -m venv /venv
ENV VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH"

# Install Poetry into the venv
RUN pip install --no-cache-dir poetry==1.8.5

# Configure Poetry to install into the active environment (/venv)
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Copy only dependency files first (better layer caching)
COPY pyproject.toml poetry.lock ./

# Install runtime dependencies into /venv
RUN poetry install --only main --no-root --no-ansi

# Copy application code
COPY . /app

# Stage 2: Runtime stage - Google distroless Python image
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# Copy the prebuilt venv + application
COPY --from=builder /venv /venv
COPY --from=builder --chown=nonroot:nonroot /app /app

# Environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH"

USER nonroot

ENTRYPOINT ["python", "main.py"]
