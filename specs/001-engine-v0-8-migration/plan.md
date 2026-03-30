# Implementation Plan: Engine v0.8.0 Migration — Provider & Architecture Consolidation

**Branch**: `001-engine-v0-8-migration` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-engine-v0-8-migration/spec.md`

## Summary

Migrate the expert engine from Azure-hosted OpenAI/Mistral providers to direct Mistral API + Scaleway embeddings, consolidate the local `prompt_graph/` package into the base engine library v0.8.0, clean up configuration and dependencies, add structured logging with proper log levels, introduce a pytest test suite targeting >90% coverage, and add a GitHub Actions CI pipeline for linting and testing.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: alkemio-virtual-contributor-engine v0.8.0, aio-pika 9.5.7, pydantic 2.11.9, load-dotenv 0.1.0
**Storage**: ChromaDB (vector database, accessed via base library)
**Testing**: pytest, pytest-cov, pytest-asyncio (new — to be added as dev dependencies)
**Target Platform**: Linux containers (Docker), macOS ARM64 for CI
**Project Type**: Message-driven async service
**Performance Goals**: N/A (no change to runtime performance characteristics)
**Constraints**: All external calls (LLM, embeddings, vector DB) mocked in tests; CI on self-hosted macOS ARM64 M4 runner
**Scale/Scope**: ~5 source files, ~300 lines of application code; test suite will roughly double the codebase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Knowledge-Grounded Responses | PASS | No change to grounding behavior. `retrieve` node still fetches from BoK exclusively. |
| II | Async Message-Driven Architecture | PASS | Request handling remains fully async via aio-pika/RabbitMQ. No sync endpoints introduced. |
| III | Source Attribution & Scoring | PASS | Response structure preserved: sources with scores (0–10), language metadata, document URIs. |
| IV | Observability | PASS | Improved: adding structured logging with INFO/DEBUG levels, invocation timing, response summaries. LangSmith tracing preserved. |
| V | Security & Prompt Integrity | PASS | No prompt changes. Credentials remain env-var-only. Old Azure keys removed from `.env.default`. |

**Technology Stack**: Migration from Azure to Mistral/Scaleway is an explicit provider change within the constitution's allowed stack. Base library upgrade to v0.8.0 is a minor version bump of an existing dependency. Python 3.11→3.12 aligns with constitution requirement (3.12+).

**Development Workflow**: Feature branch workflow followed. `.env.default` will be updated with new variable placeholders. Poetry lockfile regenerated.

**All gates pass. No violations to justify.**

## Project Structure

### Documentation (this feature)

```text
specs/001-engine-v0-8-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.
├── ai_adapter.py        # Core invocation logic (MODIFY)
├── config.py            # Configuration loading (MODIFY — clean up obsolete vars)
├── main.py              # Entry point / request handler (MODIFY — logging cleanup)
├── utils.py             # Utility functions (MODIFY — already simplified)
├── prompts.py           # Prompt templates (NO CHANGE)
├── pyproject.toml       # Dependencies (MODIFY)
├── poetry.lock          # Lockfile (REGENERATE)
├── .env.default         # Env var documentation (MODIFY — already updated)
├── Dockerfile           # Container build (ALREADY UPDATED)
├── .flake8              # Linting config (NO CHANGE)
├── .github/
│   └── workflows/
│       ├── build-deploy-k8s-*.yml    # Existing deploy workflows (NO CHANGE)
│       └── ci.yml                     # NEW — lint + test pipeline
├── tests/
│   ├── __init__.py                    # NEW
│   ├── conftest.py                    # NEW — shared fixtures
│   ├── test_ai_adapter.py            # NEW — invoke tests
│   ├── test_utils.py                 # NEW — utility function tests
│   ├── test_config.py                # NEW — config loading tests
│   └── test_main.py                  # NEW — request handler tests
└── prompt_graph/                      # DELETE entirely
```

**Structure Decision**: Flat Python project (no `src/` directory) — matches existing layout. Tests added in a `tests/` directory at root. CI workflow added alongside existing deploy workflows.

## Complexity Tracking

> No Constitution Check violations. No entries needed.
