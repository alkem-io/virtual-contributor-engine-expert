# Feature Specification: Migrate to Engine v0.8.0 — Provider & Architecture Consolidation

**Feature Branch**: `001-engine-v0-8-migration`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Migrate to alkemio-virtual-contributor-engine v0.8.0: replace Azure providers with Mistral + Scaleway, consolidate prompt graph into base library."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Expert Engine Answers Questions Using New Providers (Priority: P1)

A platform user sends a question to a virtual contributor powered by the expert engine. The engine retrieves relevant documents from the knowledge base using Scaleway-hosted embeddings instead of Azure OpenAI embeddings, generates an answer using the direct Mistral API instead of Azure-hosted Mistral, and returns a response with source citations and relevance scores. The user experience is identical to before — the migration is invisible to end users.

**Why this priority**: This is the core value of the engine. If the provider migration breaks question answering, nothing else matters. It validates that the new Mistral + Scaleway provider chain produces equivalent-quality responses.

**Independent Test**: Deploy the migrated engine with valid Mistral and Scaleway credentials, send a question against an existing Body of Knowledge, and verify a grounded response is returned with source attributions and relevance scores.

**Acceptance Scenarios**:

1. **Given** a deployed engine with Mistral API and Scaleway embeddings configured, **When** a user sends a question via the message queue, **Then** the engine returns a response containing an answer derived from the BoK, source documents with relevance scores (0–10), and language metadata.
2. **Given** a deployed engine with valid credentials, **When** a user sends a question for which the BoK has no relevant information, **Then** the engine returns a response indicating it cannot answer, without hallucinating content.
3. **Given** the old Azure-based environment variables are absent, **When** the engine starts, **Then** it initializes successfully using only the new `MISTRAL_*` and `EMBEDDINGS_*` variables.

---

### User Story 2 - Prompt Graph Runs from Base Library (Priority: P2)

A platform operator deploys the updated engine. The prompt graph — previously maintained as a local package with 6+ files — now runs entirely from the base engine library (v0.8.0). The local `prompt_graph/` directory no longer exists. The graph compiles and executes with an externally provided LLM and special node functions (e.g., `retrieve` for knowledge loading).

**Why this priority**: Consolidating the prompt graph into the base library eliminates duplication across engine variants and ensures consistent behavior. This must work for the engine to produce answers at all.

**Independent Test**: Remove the local `prompt_graph/` package, import `PromptGraph` from the base library, compile the graph with the Mistral model and `retrieve` node, invoke it with a sample input, and verify the graph executes all nodes and produces a final answer.

**Acceptance Scenarios**:

1. **Given** the local `prompt_graph/` package is deleted, **When** the engine imports `PromptGraph` from the base library, **Then** the import succeeds and the graph can be compiled with an LLM and special nodes.
2. **Given** a compiled prompt graph with a `retrieve` special node, **When** the graph is streamed with a user message and BoK ID, **Then** each graph step completes and logs individually, the `retrieve` node fetches documents from the vector database, and the accumulated result contains `final_answer`, `knowledge_docs`, and `source_scores`.

---

### User Story 3 - Test Suite with >90% Coverage (Priority: P3)

A developer runs the test suite and receives a coverage report showing above 90% line coverage across the codebase. Tests cover the AI adapter invocation flow (happy path and error paths), the `retrieve` special node, utility functions, configuration loading, and the request handler entry point. All external dependencies (Mistral API, Scaleway embeddings, ChromaDB, RabbitMQ) are mocked so tests run without credentials or infrastructure.

**Why this priority**: The project currently has no tests. Adding a comprehensive test suite post-migration ensures the new code is correct, prevents regressions, and enables safe future changes.

**Independent Test**: Run `pytest --cov` from the project root and verify the coverage report shows >90% line coverage with all tests passing.

**Acceptance Scenarios**:

1. **Given** the test suite is in place, **When** `pytest` is run, **Then** all tests pass and no external services are contacted.
2. **Given** the test suite with coverage enabled, **When** `pytest --cov` is run, **Then** the coverage report shows >90% line coverage.
3. **Given** a test for the invoke function with a missing `prompt_graph`, **When** the test runs, **Then** it verifies the engine returns an error response without crashing.
4. **Given** a test for the `retrieve` function, **When** the test runs with a mocked vector database, **Then** it verifies documents are fetched and combined correctly.

---

### User Story 4 - CI Pipeline with Lint and Test Steps (Priority: P4)

A developer pushes a commit or opens a pull request. A CI pipeline automatically runs linting (flake8) and the full test suite with coverage reporting. The pipeline fails if linting errors are found or if any test fails. Coverage results are visible in the CI output.

**Why this priority**: Automated quality gates prevent regressions from reaching the main branch. Without CI, linting and testing depend on developer discipline.

**Independent Test**: Push a commit to a feature branch and verify the CI pipeline runs both lint and test steps, reporting results.

**Acceptance Scenarios**:

1. **Given** a CI workflow is configured, **When** a commit is pushed or a PR is opened, **Then** the pipeline runs linting and tests automatically.
2. **Given** the CI pipeline, **When** a linting violation is present, **Then** the pipeline fails with a clear error message identifying the violation.
3. **Given** the CI pipeline, **When** all linting passes and all tests pass, **Then** the pipeline succeeds and coverage results are visible in the output.

---

### User Story 5 - Structured Logging with Appropriate Log Levels (Priority: P5)

An operator monitors the engine in production. Logs are structured with appropriate levels so that INFO provides a clear picture of request flow without noise, while DEBUG reveals full details for troubleshooting. At INFO level: the persona ID and VC name on invocation, the user query, conversation history message count, graph invocation duration, a summary of the response (answer length, source count, detected language), and any errors. At DEBUG level: the full input message payload, full conversation history content, full response content, and retrieved document details. The `pprint` call for input logging is removed in favor of structured logger calls.

**Why this priority**: The current logging is inconsistent — mixing `print`/`pprint` with logger calls, logging too much at INFO, and missing key operational data like response summaries and timing. Clean logging is essential for production observability.

**Independent Test**: Run the engine at INFO level and verify logs show request flow without full payloads. Switch to DEBUG and verify full details appear.

**Acceptance Scenarios**:

1. **Given** log level set to INFO, **When** a request is processed, **Then** logs show: persona ID, VC name, user query, history message count, each graph step completion, invocation duration in seconds, response summary (answer length, source count, language), without full input or response payloads.
2. **Given** log level set to DEBUG, **When** a request is processed, **Then** logs additionally show: full input message, full conversation history, per-step output details, full response content, and retrieved document details.
3. **Given** the updated codebase, **When** inspecting `main.py`, **Then** there are no `print()` or `pprint()` calls — all output goes through the structured logger.

---

### Edge Cases

- What happens when the LLM API key is invalid or expired? The engine MUST log the authentication error and return a user-friendly error message.
- What happens when the embeddings endpoint is unreachable? The `retrieve` node MUST fail gracefully and the engine MUST return an error rather than crash.
- What happens when a Body of Knowledge collection does not exist in the vector database? The engine MUST log the missing collection and return an appropriate "cannot answer" response.
- What happens when the `prompt_graph` field is missing from the input message? The engine MUST return an error indicating the prompt graph is required (existing behavior preserved).
- What happens when the LLM model invocation fails? The engine MUST log the error with sufficient context and return a user-friendly error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate answers using the direct Mistral API with model name configurable via environment variable.
- **FR-002**: System MUST perform semantic search using Scaleway-hosted embeddings with endpoint, API key, and model name configurable via environment variables.
- **FR-003**: System MUST import `PromptGraph` from the base engine library (v0.8.0), not from a local package.
- **FR-004**: System MUST delete the local `prompt_graph/` package entirely (all 7 files).
- **FR-005**: System MUST import shared utility functions (`history_as_conversation`, `history_as_dict`, `query_documents`, `combine_query_results`) from the base engine library.
- **FR-006**: System MUST remove all local implementations of functions now provided by the base library.
- **FR-007**: System MUST pass the conversation history directly to the prompt graph without modification (the server already includes the current message in the history).
- **FR-008**: System MUST use `graph.stream()` for prompt graph execution, accumulating results step-by-step, and log the completion of each graph step at INFO level and step output at DEBUG level.
- **FR-009**: System MUST log the total duration of the graph invocation in seconds, so operators can monitor response latency.
- **FR-010**: System MUST extract `current_question` from the first message in history and pass it as a separate field in the graph input state.
- **FR-011**: System MUST remove obsolete environment variables (`AZURE_*`, `OPENAI_*`, `AI_LOCAL_PATH`, `AI_MODEL_TEMPERATURE`, `LLM_DEPLOYMENT_NAME`, `EMBEDDINGS_DEPLOYMENT_NAME`) from the default configuration.
- **FR-012**: System MUST require Python 3.12 or higher.
- **FR-013**: System MUST remove direct dependencies on `langchain-community`, `json-schema-to-pydantic`, and `langgraph` (these become transitive via the base library).
- **FR-014**: Project MUST include a test suite using pytest that achieves >90% line coverage.
- **FR-015**: Tests MUST mock all external dependencies (LLM API, embeddings endpoint, vector database, message queue) so they run without credentials or infrastructure.
- **FR-016**: Tests MUST cover the invoke happy path, missing prompt_graph error path, LLM failure error path, retrieve node behavior, and utility functions.
- **FR-017**: Project MUST include a CI workflow (GitHub Actions) that runs on push and pull request events, using `ubuntu-latest` runner with `actions/setup-python` for Python 3.12.
- **FR-018**: CI pipeline MUST run flake8 linting and fail on any violations.
- **FR-019**: CI pipeline MUST run pytest with coverage reporting and fail if any test fails.
- **FR-020**: Project MUST add pytest, pytest-cov, and pytest-asyncio as dev dependencies.
- **FR-021**: System MUST log at INFO level: persona ID and VC name on invocation, user query, conversation history message count, graph invocation duration, per-step completion, and response summary (answer length, source count, detected language).
- **FR-022**: System MUST log at DEBUG level: full input message payload, full conversation history content, per-step output, full response content, and retrieved document details.
- **FR-023**: System MUST NOT use `print()` or `pprint()` for output — all logging MUST go through the structured logger.
- **FR-024**: System MUST NOT log the full input message at INFO level — only query and metadata.

### Key Entities

- **Special Nodes**: Named functions (e.g., `retrieve`) injected into the prompt graph at compile time, enabling graph nodes to call engine-specific logic like knowledge retrieval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Engine answers user questions with equivalent quality and response structure (answer, sources, scores, language metadata) after migration — no regression in response format.
- **SC-002**: Engine starts and processes requests successfully with only the new environment variables, without any legacy Azure or OpenAI variables present.
- **SC-003**: Local `prompt_graph/` package is fully removed with zero remaining local imports — all graph functionality sourced from the base library.
- **SC-004**: Total direct dependency count in `pyproject.toml` decreases by 3 (removal of `langchain-community`, `json-schema-to-pydantic`, `langgraph`).
- **SC-005**: Test suite achieves >90% line coverage as reported by pytest-cov.
- **SC-006**: All tests pass without requiring any external services, API keys, or network access.
- **SC-007**: CI pipeline runs linting and tests on every push and PR, blocking merge on failure.
- **SC-008**: At INFO level, each request produces logs covering invocation metadata, query, timing, and response summary — without full payloads.
- **SC-009**: Zero `print()`/`pprint()` calls remain in the codebase — all output uses the structured logger.

## Assumptions

- The base engine library v0.8.0 is stable and its exported API (`PromptGraph`, `query_documents`, `combine_query_results`, `history_as_conversation`, `history_as_dict`, `mistral_small`) is finalized.
- Existing vector database collections and document formats are compatible with the new `query_documents()` function from the base library.
- The Mistral API and Scaleway embeddings endpoint provide equivalent or better quality compared to the previous Azure-hosted services.
- The prompt graph JSON definition format consumed by the base library is backward-compatible with existing stored prompt graph configurations.
- The server (upstream platform) includes the current user message in the history before dispatching to the engine — the engine does not need to append it.
