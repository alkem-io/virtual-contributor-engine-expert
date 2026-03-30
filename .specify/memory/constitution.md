<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: none
- Added principles:
  6. Test Coverage (new)
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed (generic)
  - .specify/templates/spec-template.md ✅ no changes needed (generic)
  - .specify/templates/tasks-template.md ✅ no changes needed (tests already supported)
  - .specify/templates/commands/ ✅ no command files present
- Follow-up TODOs: none
-->

# Virtual Contributor Engine Expert Constitution

## Core Principles

### I. Knowledge-Grounded Responses

All generated answers MUST be derived exclusively from the Body of Knowledge (BoK)
stored in the vector database. The system MUST NOT hallucinate, speculate, or
supplement answers with information outside the retrieved documents. When the BoK
contains insufficient information to answer a query, the system MUST explicitly
state that it cannot answer rather than fabricate a response.

**Rationale**: The engine serves as a trusted expert persona for Alkemio
collaboration spaces. Ungrounded answers erode trust and may propagate
misinformation within the platform.

### II. Async Message-Driven Architecture

All request handling MUST be fully asynchronous, using RabbitMQ as the message
broker. The engine MUST NOT expose synchronous HTTP endpoints or block the event
loop. New features MUST integrate with the existing `aio-pika` message consumer
pattern and the `alkemio-virtual-contributor-engine` base library.

**Rationale**: The engine runs as one of potentially many virtual contributors
within the Alkemio platform. Async message-driven design ensures the system
scales horizontally and integrates cleanly with the platform's event bus.

### III. Source Attribution & Scoring

Every response MUST include the source documents used to generate the answer,
each with a relevance score (0–10 scale). Source metadata MUST include document
type, title, and URI. Responses MUST also include language detection metadata
(ISO-639-1 format) for both the question and the answer.

**Rationale**: Users and downstream systems rely on source attribution to
evaluate answer quality and trace information provenance. Scoring enables
filtering and ranking of results by consuming services.

### IV. Observability

All LLM interactions MUST be traceable via LangSmith (or equivalent tracing
backend). The system MUST use structured logging at appropriate levels. New
features MUST NOT degrade existing tracing or logging coverage. Error conditions
MUST produce actionable log entries with sufficient context for debugging.

**Rationale**: LLM-based systems are inherently non-deterministic. Without
end-to-end observability, diagnosing quality regressions, latency issues, or
incorrect answers becomes impractical in production.

### V. Security & Prompt Integrity

The system MUST enforce prompt boundaries that prevent user input from
overriding system instructions or persona definitions. The combined prompt
MUST constrain the LLM to respond only within the defined persona and BoK
scope. New prompt modifications MUST be reviewed for injection vulnerabilities.
Sensitive configuration (API keys, credentials) MUST be loaded from environment
variables or secrets — never hardcoded.

**Rationale**: The engine processes untrusted user input and passes it to an
LLM. Without prompt integrity enforcement, adversarial inputs could bypass
knowledge grounding, leak system prompts, or cause the persona to behave
outside its intended role.

### VI. Test Coverage

All production code MUST maintain a minimum of 90% test coverage as measured by
line coverage (`pytest --cov`). New features and bug fixes MUST include tests
that cover the changed code paths. Coverage MUST NOT decrease on any pull
request — if a PR reduces coverage below the 90% threshold, it MUST be blocked
until tests are added. Critical paths (prompt graph execution, response
building, message handling) SHOULD target 95%+ coverage.

**Rationale**: The engine relies on non-deterministic LLM interactions and
async message processing, making untested code paths high-risk for silent
regressions. A strict coverage floor ensures that refactors, dependency
upgrades, and prompt changes are validated against known-good behavior.

## Technology Stack Constraints

- **Language**: Python 3.12+
- **LLM Provider**: Mistral AI (mistral-small-latest or as configured)
- **Embeddings**: Scaleway-hosted model (Qwen3-Embedding-8B or as configured)
- **Vector Database**: ChromaDB for document storage and semantic retrieval
- **Message Queue**: RabbitMQ via aio-pika (async)
- **Orchestration**: LangChain for prompt graph compilation and execution
- **Base Library**: `alkemio-virtual-contributor-engine` — engine lifecycle,
  message handling, and shared types
- **Validation**: Pydantic for all data models
- **Containerization**: Docker (multi-arch: x86_64, arm64), deployed on
  Kubernetes via Scaleway container registry
- **License**: EUPL-1.2

Changes to the core technology stack (LLM provider, vector DB, message broker,
or base library) MUST be treated as a major architectural decision requiring
explicit justification and a migration plan.

## Development Workflow

- All changes MUST be developed on feature branches and merged via pull request
  into `develop`.
- Version bumps follow semantic versioning (MAJOR.MINOR.PATCH).
- The `Dockerfile` MUST remain buildable and produce a working container after
  every merge to `develop`.
- Environment configuration MUST be documented in `.env.default` with sensible
  placeholder values for all required variables.
- Dependencies are managed via Poetry (`pyproject.toml` / `poetry.lock`).
  Dependency additions or upgrades MUST not break the existing lock file
  without explicit intent.

## Governance

This constitution defines the non-negotiable principles for the
virtual-contributor-engine-expert project. All feature specifications,
implementation plans, and code changes MUST be evaluated against these
principles.

**Amendment procedure**:
1. Propose the change with rationale in a pull request modifying this file.
2. Document the version bump (MAJOR for principle removal/redefinition,
   MINOR for new principles or material expansion, PATCH for clarifications).
3. Update the Sync Impact Report at the top of this file.
4. Verify dependent templates still align with updated principles.

**Compliance**: All PRs and reviews SHOULD verify that changes do not violate
the core principles. The Constitution Check section in implementation plans
MUST reference these principles by number.

**Version**: 1.1.0 | **Ratified**: 2026-03-26 | **Last Amended**: 2026-03-27
