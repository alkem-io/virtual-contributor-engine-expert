# Quickstart: Engine v0.8.0 Migration

**Date**: 2026-03-26
**Feature**: [spec.md](./spec.md)

## Prerequisites

- Python 3.12+
- Poetry 2.x
- Access to Mistral API key
- Access to Scaleway embeddings endpoint
- Running RabbitMQ instance
- Running ChromaDB instance with at least one BoK collection

## Setup

1. **Clone and checkout the branch**:
   ```bash
   git checkout 001-engine-v0-8-migration
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Configure environment**:
   ```bash
   cp .env.default .env
   # Edit .env with your actual credentials:
   # - MISTRAL_API_KEY
   # - MISTRAL_SMALL_MODEL_NAME (default: mistral-small-latest)
   # - EMBEDDINGS_API_KEY
   # - EMBEDDINGS_ENDPOINT
   # - EMBEDDINGS_MODEL_NAME
   # - RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD
   # - VECTOR_DB_HOST, VECTOR_DB_PORT
   # - LANGCHAIN_API_KEY
   ```

4. **Run the engine**:
   ```bash
   python main.py
   ```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov --cov-report=term-missing

# Run a specific test file
poetry run pytest tests/test_ai_adapter.py -v
```

## Running Linting

```bash
poetry run flake8
```

## Verification Checklist

- [ ] Engine starts without import errors
- [ ] No `AZURE_*` or `OPENAI_*` variables referenced
- [ ] `prompt_graph/` directory does not exist
- [ ] `poetry run pytest` — all tests pass
- [ ] `poetry run pytest --cov` — >90% line coverage
- [ ] `poetry run flake8` — no violations
- [ ] Send a test message via RabbitMQ and verify response includes answer, sources, and language metadata
