# Research: Engine v0.8.0 Migration

**Date**: 2026-03-26
**Feature**: [spec.md](./spec.md)

## R1: Base Library v0.8.0 API Surface

**Decision**: Import `PromptGraph`, `query_documents`, `combine_query_results`, `history_as_conversation`, `history_as_dict`, `mistral_small`, `HistoryItem`, `MessageSenderRole` from `alkemio-virtual-contributor-engine`.

**Rationale**: The v0.8.0 release absorbs the prompt graph implementation and utility functions previously maintained locally. The git tag `v0.8.0` is confirmed in `pyproject.toml`. All required exports are already used in the working diff.

**Alternatives considered**:
- Keep local `prompt_graph/` and pin to v0.7.0 → rejected: duplicates code across engine variants, increases maintenance burden.

## R2: Provider Configuration

**Decision**: Replace Azure OpenAI + Azure Mistral with direct Mistral API (`MISTRAL_API_KEY`, `MISTRAL_SMALL_MODEL_NAME`) and Scaleway embeddings (`EMBEDDINGS_API_KEY`, `EMBEDDINGS_ENDPOINT`, `EMBEDDINGS_MODEL_NAME`).

**Rationale**: Provider initialization is handled by the base library via these env vars. The base library's `mistral_small` object reads `MISTRAL_API_KEY` and `MISTRAL_SMALL_MODEL_NAME` at import time. Scaleway embeddings are configured via the `EMBEDDINGS_*` variables used by `query_documents()`.

**Alternatives considered**:
- Keep Azure Mistral endpoint → rejected: moving away from Azure dependency, Scaleway is the target infrastructure.
- Use OpenAI-compatible API → rejected: Mistral native SDK provides better integration.

## R3: config.py Cleanup

**Decision**: Remove obsolete config entries (`openai_*`, `mistral_*` Azure variants, `model_temperature`, `llm_deployment_name`, `embeddings_deployment_name`, `local_path`, `source_website`) and derived variables (`local_path`, `vectordb_path`, `chunk_size`, `max_token_limit`). Keep only `LOG_LEVEL`, `HISTORY_LENGTH`, and RabbitMQ settings that are still referenced.

**Rationale**: The base library now owns provider configuration. The local `config` dict contained 15 entries; most are now unused. Keeping dead config creates confusion about what the engine actually needs.

**Alternatives considered**:
- Keep full config dict for backward compatibility → rejected: no consumers of the removed keys remain.

## R4: Testing Strategy

**Decision**: Use pytest + pytest-asyncio for async test support, pytest-cov for coverage. Mock all externals using `unittest.mock.patch`. Structure: `tests/` at project root with one test file per source module.

**Rationale**: pytest is the de facto Python testing standard. pytest-asyncio handles the async `invoke()` function. Mocking at the import boundary (base library functions) keeps tests fast and infrastructure-free.

**Alternatives considered**:
- Integration tests with real ChromaDB → rejected: adds infra dependency, not suitable for CI without Docker services.
- Use `responses` or `httpx_mock` → rejected: we mock at the Python function level, not HTTP level, since the base library abstracts the HTTP calls.

## R5: CI Pipeline Design

**Decision**: Add `.github/workflows/ci.yml` with a single job running on `ubuntu-latest` using `actions/setup-python@v5` for Python 3.12. Steps: checkout, setup Python, install Poetry, install dependencies, run flake8, run pytest with coverage. Triggered on push and pull_request to all branches.

**Rationale**: GitHub-hosted `ubuntu-latest` provides a reliable, zero-maintenance CI environment. Single job is sufficient — lint and test are fast enough to run sequentially. Existing deploy workflows remain unchanged (they trigger only on `develop` push).

**Alternatives considered**:
- Separate lint and test jobs → rejected: overhead of two jobs outweighs parallelism benefit for this small project.
- Use self-hosted macOS ARM64 runner → rejected: `actions/setup-python` fails with permission errors on the self-hosted runner (`/Users/runner` path mismatch), and `pip install` puts binaries outside `$PATH`. Filed alkem-io/virtual-contributor-engine#33 to investigate runner fixes across all VC projects.

## R6: Logging Structure

**Decision**: Replace `print()`/`pprint()` in `main.py` with structured logger calls. Add timing around graph invocation in `ai_adapter.py`. Log levels:
- **INFO**: persona ID, VC name, user query, history message count, invocation duration, response summary (answer length, source count, language).
- **DEBUG**: full input payload, full conversation history, full response, retrieved document details.
- **ERROR**: exceptions with full stack traces (already handled by `logger.exception()`).

**Rationale**: Production operators need request flow visibility at INFO without payload noise. Developers debugging issues need full payloads at DEBUG. The current mix of `print`/`pprint`/`logger` is inconsistent and logs too much at INFO.

**Alternatives considered**:
- JSON structured logging (e.g., `structlog`) → rejected: over-engineering for current scale; `setup_logger` from base library provides adequate formatting.
- Log response at INFO level in full → rejected: responses can be large and contain user-specific content; summary is sufficient for operational monitoring.
