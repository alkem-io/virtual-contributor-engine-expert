# Data Model: Engine v0.8.0 Migration

**Date**: 2026-03-26
**Feature**: [spec.md](./spec.md)

## Overview

This migration does not introduce new data entities. The existing data model is preserved — the change is in which layer owns the implementations. All models below are defined in the base library (`alkemio-virtual-contributor-engine` v0.8.0) and consumed by the expert engine.

## Entities (from base library)

### Input

Incoming request message from the platform via RabbitMQ.

| Field | Type | Description |
|-------|------|-------------|
| message | string | The user's current question |
| history | list[HistoryItem] | Previous conversation messages |
| prompt_graph | dict | JSON definition of the prompt graph to execute |
| body_of_knowledge_id | string | Identifier for the BoK collection in ChromaDB |
| persona_id | string | AI persona identifier |
| display_name | string | Virtual contributor display name |
| description | string | Persona description for prompt context |

### HistoryItem

A single message in the conversation history.

| Field | Type | Description |
|-------|------|-------------|
| content | string | Message text |
| role | MessageSenderRole | HUMAN or AI |

### Response

Outgoing response message returned to the platform.

| Field | Type | Description |
|-------|------|-------------|
| result | string | The generated answer |
| original_result | string | Raw knowledge-based answer before post-processing |
| sources | list[dict] | Source documents with score, URI, title |
| human_language | string | Detected language of the question (ISO-639-1) |
| result_language | string | Language of the answer (ISO-639-1) |
| knowledge_language | string | Language of the knowledge base content (ISO-639-1) |
| source_scores | dict | Raw score mapping (index → score) |

### PromptGraph (from base library)

Compiled graph definition that orchestrates LLM calls and special nodes.

| Method | Description |
|--------|-------------|
| `from_dict(data)` | Parse a JSON graph definition into a PromptGraph instance |
| `compile(llm, special_nodes)` | Compile the graph with a given LLM model and special node functions |

### Special Node: retrieve

Engine-specific function injected into the graph at compile time.

| Input (from state) | Output |
|---------------------|--------|
| `state.rephrased_question` or last message content | `knowledge_docs`: raw ChromaDB query result |
| `state.bok_id` | `combined_knowledge_docs`: formatted document text |

## Data Flow

```
RabbitMQ message
  → Input (Pydantic model)
    → full_history = history + current message
      → PromptGraph.compile(llm=mistral_small, special_nodes={retrieve})
        → graph.invoke({messages, conversation, bok_id, description, display_name})
          → retrieve node: query ChromaDB → knowledge_docs
          → LLM node: generate answer from knowledge + conversation
          → result: {final_answer, knowledge_docs, source_scores, languages}
    → build Response with sources, scores, language metadata
  → Response (Pydantic model)
→ RabbitMQ result queue
```
