# virtual-contributor-engine-expert Development Guidelines

## Project Overview

AI-powered expert engine for the Alkemio platform. Receives questions via RabbitMQ, retrieves relevant documents from ChromaDB using Scaleway embeddings, generates answers using Mistral AI, and returns responses with source citations and relevance scores.

## Active Technologies

- Python 3.12+
- alkemio-virtual-contributor-engine v0.8.0 (base library)
- aio-pika 9.5.7 (RabbitMQ async client)
- Pydantic 2.11.9 (data validation)
- ChromaDB (vector database)
- Mistral AI (LLM provider)
- LangChain / LangSmith (orchestration + tracing)

## Project Structure

```text
.
├── ai_adapter.py        # Core invocation logic (prompt graph + response building)
├── config.py            # Environment variable loading
├── main.py              # Entry point, request handler, engine bootstrap
├── utils.py             # Knowledge loading, logging helpers
├── prompts.py           # Prompt templates
├── pyproject.toml       # Dependencies (Poetry)
├── Dockerfile           # Multi-stage container build
├── .env.default         # Environment variable documentation
├── .flake8              # Linting configuration
├── tests/               # pytest test suite
└── .github/workflows/   # CI/CD pipelines
```

## Commands

```bash
# Install dependencies
poetry install

# Run the engine
poetry run python main.py

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov --cov-report=term-missing

# Run linting
poetry run flake8
```

## Code Style

- Follow flake8 rules (max-line-length=100, see `.flake8`)
- Use `setup_logger(__name__)` for all logging — never `print()`/`pprint()`
- All async request handling via aio-pika — no sync HTTP endpoints
- External dependencies (LLM, embeddings, vector DB) are accessed via the base library

## Key Patterns

- `PromptGraph.from_dict()` → `compile(llm=, special_nodes=)` → `graph.invoke()`
- Special nodes (e.g., `retrieve`) are injected at compile time
- All provider config via environment variables — never hardcoded
- Response always includes: answer, sources with scores, language metadata

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
