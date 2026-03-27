# Tasks: Engine v0.8.0 Migration — Provider & Architecture Consolidation

**Input**: Design documents from `/specs/001-engine-v0-8-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Yes — User Story 3 explicitly requests a test suite with >90% coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency updates and project configuration changes shared across all stories

- [x] T001 Update base library dependency to v0.8.0 and Python requirement to ^3.12 in pyproject.toml
- [x] T002 Remove direct dependencies `langchain-community`, `json-schema-to-pydantic`, and `langgraph` from pyproject.toml
- [x] T003 Add dev dependencies `pytest`, `pytest-cov`, and `pytest-asyncio` to pyproject.toml
- [x] T004 Regenerate poetry.lock by running `poetry lock && poetry install`
- [x] T005 [P] Update .env.default: replace Azure/OpenAI vars with MISTRAL_* and EMBEDDINGS_* variables, remove AI_LOCAL_PATH, AI_MODEL_TEMPERATURE, LLM_DEPLOYMENT_NAME, EMBEDDINGS_DEPLOYMENT_NAME
- [x] T006 [P] Create tests/ directory with __init__.py at tests/__init__.py

**Checkpoint**: Dependencies updated, dev tooling available, environment config reflects new providers.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core cleanup that MUST be complete before user story work can proceed

**⚠️ CRITICAL**: User stories depend on the base library v0.8.0 being installed (T004) and obsolete config being removed.

- [x] T007 Clean up config.py: remove all obsolete entries (openai_*, mistral Azure variants, model_temperature, llm_deployment_name, embeddings_deployment_name, local_path, source_website) and derived variables (local_path, vectordb_path, chunk_size, max_token_limit). Keep only LOG_LEVEL, HISTORY_LENGTH, and RabbitMQ settings.
- [x] T008 Delete the entire prompt_graph/ directory (7 files: __init__.py, edge.py, node.py, state.py, prompt_graph.py, json_graph_parser.py, prompt.graph.expert.example.json)

**Checkpoint**: Obsolete code and config removed. Base library v0.8.0 is the sole source of prompt graph and provider functionality.

---

## Phase 3: User Story 1 — Expert Engine Answers Questions Using New Providers (Priority: P1) 🎯 MVP

**Goal**: Engine generates answers using direct Mistral API + Scaleway embeddings, with no Azure dependencies.

**Independent Test**: Send a question via RabbitMQ against an existing BoK and verify the response contains an answer, sources with scores, and language metadata.

### Implementation for User Story 1

- [x] T009 [US1] Update ai_adapter.py imports: import PromptGraph, mistral_small, combine_query_results, HistoryItem, MessageSenderRole from alkemio-virtual-contributor-engine base library instead of local prompt_graph
- [x] T010 [US1] Update utils.py imports: import query_documents, combine_query_results, history_as_conversation, history_as_dict from base library; remove local implementations of history_as_conversation, history_as_dict, load_documents, combine_documents
- [x] T011 [US1] Update ai_adapter.py invoke function: compile graph with `prompt_graph.compile(llm=mistral_small, special_nodes={"retrieve": retrieve})`, append current message to history before invocation
- [x] T012 [US1] Implement retrieve special node function in ai_adapter.py: extract last message from state, call load_knowledge, call combine_query_results, return knowledge_docs and combined_knowledge_docs
- [x] T013 [US1] Verify .env.default contains all required new variables (MISTRAL_API_KEY, MISTRAL_SMALL_MODEL_NAME, EMBEDDINGS_API_KEY, EMBEDDINGS_ENDPOINT, EMBEDDINGS_MODEL_NAME) with placeholder values

**Checkpoint**: Engine answers questions using Mistral + Scaleway. No Azure variables referenced. Response format unchanged.

---

## Phase 4: User Story 2 — Prompt Graph Runs from Base Library (Priority: P2)

**Goal**: All prompt graph functionality comes from the base library. Zero local prompt_graph/ imports remain.

**Independent Test**: Verify no imports reference `prompt_graph` as a local package. PromptGraph is imported from `alkemio_virtual_contributor_engine`.

### Implementation for User Story 2

- [x] T014 [US2] Verify prompt_graph/ directory is fully deleted (T008) and no residual imports of `from prompt_graph import ...` exist anywhere in the codebase
- [x] T015 [US2] Verify ai_adapter.py uses PromptGraph.from_dict() from base library and compile() accepts llm and special_nodes parameters
- [x] T016 [US2] Remove any commented-out code referencing old prompt_graph module in utils.py (load_context commented block)

**Checkpoint**: Prompt graph fully sourced from base library. No local prompt_graph references remain.

---

## Phase 5: User Story 5 — Structured Logging with Appropriate Log Levels (Priority: P5)

**Goal**: Clean, structured logging with INFO for operational visibility and DEBUG for troubleshooting. No print()/pprint() calls.

**Independent Test**: Run the engine at INFO level — logs show request metadata, query, timing, and response summary without full payloads. At DEBUG — full details appear.

> **Note**: Logging (US5) is implemented before testing (US3) because the test suite will validate the logging behavior.

### Implementation for User Story 5

- [x] T017 [US5] Update main.py: remove `from pprint import pprint` and `print()`/`pprint()` calls. Replace with structured logger calls — INFO for persona ID, VC name, user query; DEBUG for full input payload
- [x] T018 [US5] Update main.py on_request: log response summary at INFO level (answer length, source count, detected language) after invoke returns
- [x] T019 [US5] Add invocation timing in ai_adapter.py: wrap graph.invoke() with time.time() and log duration at INFO level (e.g., "Graph invocation completed in {duration:.2f}s")
- [x] T020 [US5] Add DEBUG logging in ai_adapter.py: log full conversation history before invocation, log history message count at INFO
- [x] T021 [US5] Add DEBUG logging in ai_adapter.py: log full response content and retrieved document details after invocation
- [x] T022 [US5] Verify zero print()/pprint() calls remain in the entire codebase (grep for `print(` and `pprint(`)

**Checkpoint**: Structured logging in place. INFO shows request flow concisely. DEBUG shows full details. No print() calls remain.

---

## Phase 6: User Story 3 — Test Suite with >90% Coverage (Priority: P3)

**Goal**: Comprehensive pytest test suite covering all modules with >90% line coverage. All externals mocked.

**Independent Test**: Run `poetry run pytest --cov --cov-report=term-missing` and verify >90% coverage with all tests passing.

### Implementation for User Story 3

- [x] T023 [US3] Create tests/conftest.py with shared fixtures: mock Input object, mock PromptGraph, mock graph.invoke result with realistic data (final_answer, knowledge_docs, source_scores, languages), mock Response
- [x] T024 [P] [US3] Create tests/test_ai_adapter.py: test invoke happy path (mocked graph returns answer with sources), test missing prompt_graph returns error response, test graph invocation failure returns error response, test retrieve function with mocked query_documents, test source score filtering and title formatting
- [x] T025 [P] [US3] Create tests/test_utils.py: test load_knowledge calls query_documents with correct collection name and num_docs=4, test log_docs with valid docs logs IDs at INFO and full docs at DEBUG, test log_docs with empty/missing docs does not crash
- [x] T026 [P] [US3] Create tests/test_config.py: test LOG_LEVEL assertion with valid values, test config loads with expected env var defaults
- [x] T027 [P] [US3] Create tests/test_main.py: test on_request calls ai_adapter.invoke and returns Response, test logging output at INFO level includes persona ID and VC name
- [x] T028 [US3] Run `poetry run pytest --cov --cov-report=term-missing` and verify >90% line coverage. If below target, add additional tests to cover missed lines.
- [x] T029 [US3] Run `poetry run flake8` and fix any linting violations in test files

**Checkpoint**: All tests pass. >90% coverage achieved. Linting clean.

---

## Phase 7: User Story 4 — CI Pipeline with Lint and Test Steps (Priority: P4)

**Goal**: GitHub Actions workflow that lints and tests on every push and PR, using the self-hosted macOS ARM64 M4 runner.

**Independent Test**: Push a commit and verify the CI pipeline runs lint + test steps and reports results.

### Implementation for User Story 4

- [x] T030 [US4] Create .github/workflows/ci.yml: trigger on push and pull_request to all branches, single job on `[self-hosted, macOS, ARM64, apple-silicon, m4]` runner
- [x] T031 [US4] Add CI steps: checkout, setup Python 3.12, install Poetry, run `poetry install`, run `poetry run flake8`, run `poetry run pytest --cov --cov-report=term-missing`
- [x] T032 [US4] Verify CI workflow YAML is valid and flake8-clean

**Checkpoint**: CI pipeline runs on every push/PR. Linting and tests gate merges.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all stories

- [x] T033 [P] Run full linting pass: `poetry run flake8` — fix any remaining violations
- [x] T034 [P] Run full test pass with coverage: `poetry run pytest --cov --cov-report=term-missing` — verify >90%
- [x] T035 Verify .env.default documents all required variables with sensible placeholders
- [x] T036 Verify Dockerfile builds successfully with the updated dependencies
- [x] T037 Run quickstart.md verification checklist end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T004 (poetry install) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase completion
- **US2 (Phase 4)**: Depends on T008 (prompt_graph deletion) and US1 (import updates)
- **US5 (Phase 5)**: Depends on US1 (ai_adapter.py is stable)
- **US3 (Phase 6)**: Depends on US1, US2, US5 (code must be final before writing tests)
- **US4 (Phase 7)**: Depends on US3 (tests must exist for CI to run them)
- **Polish (Phase 8)**: Depends on all stories complete

### Execution Order

```
Phase 1 (Setup) → Phase 2 (Foundational)
  → Phase 3 (US1: Providers) → Phase 4 (US2: Prompt Graph)
    → Phase 5 (US5: Logging) → Phase 6 (US3: Tests)
      → Phase 7 (US4: CI) → Phase 8 (Polish)
```

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:

- **Phase 1**: T005 + T006 (env config + test dir) in parallel
- **Phase 6**: T024 + T025 + T026 + T027 (all test files) in parallel
- **Phase 8**: T033 + T034 (lint + test runs) in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Engine answers questions with new providers
5. Deploy to dev if ready

### Incremental Delivery

1. Setup + Foundational → Dependencies ready
2. US1 (Providers) → Core migration working → Deploy/Demo (MVP!)
3. US2 (Prompt Graph) → Consolidation verified
4. US5 (Logging) → Observability improved
5. US3 (Tests) → Quality assured with >90% coverage
6. US4 (CI) → Automated quality gates in place
7. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US5 (Logging) is ordered before US3 (Tests) so tests can validate logging behavior
- All test files mock external dependencies — no network access needed
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
