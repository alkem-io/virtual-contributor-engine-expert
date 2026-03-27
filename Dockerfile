# Stage 1: Build stage - Python 3.12 (required by pyproject.toml)
FROM python:3.12-slim-bookworm AS builder

# Install git (required for git-based Poetry deps)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

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

# Stage 2: Runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy the prebuilt venv + application
COPY --from=builder /venv /venv
COPY --from=builder /app /app

# Environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser
USER appuser

ENTRYPOINT ["python", "main.py"]
