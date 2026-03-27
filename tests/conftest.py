import pytest
from unittest.mock import MagicMock
from alkemio_virtual_contributor_engine import (
    Input, HistoryItem, MessageSenderRole,
)
from alkemio_virtual_contributor_engine.events.input import (
    ResultHandler, ResultHandlerAction,
)


@pytest.fixture
def mock_input():
    """Create a realistic mock Input object."""
    return Input(
        engine="expert",
        userID="user-123",
        message="What is Alkemio?",
        bodyOfKnowledgeID="bok-abc",
        contextID="ctx-1",
        history=[
            HistoryItem(content="Hello", role=MessageSenderRole.HUMAN),
            HistoryItem(content="Hi there!", role=MessageSenderRole.ASSISTANT),
        ],
        displayName="Test VC",
        description="A test virtual contributor",
        personaID="persona-456",
        resultHandler=ResultHandler(action=ResultHandlerAction.POST_REPLY),
        promptGraph={
            "nodes": [{"id": "start", "type": "start"}],
            "edges": [],
        },
    )


@pytest.fixture
def mock_input_no_graph():
    """Create an Input with no prompt_graph."""
    return Input(
        engine="expert",
        userID="user-123",
        message="What is Alkemio?",
        bodyOfKnowledgeID="bok-abc",
        contextID="ctx-1",
        history=[],
        displayName="Test VC",
        description="A test virtual contributor",
        personaID="persona-456",
        resultHandler=ResultHandler(action=ResultHandlerAction.POST_REPLY),
        promptGraph=None,
    )


@pytest.fixture
def mock_graph_result():
    """Realistic graph invocation result."""
    return {
        "final_answer": "Alkemio is a collaboration platform.",
        "knowledge_answer": "Alkemio is a collaboration platform.",
        "human_language": "en",
        "knowledge_language": "en",
        "knowledge_docs": {
            "ids": [["doc-1", "doc-2"]],
            "documents": [["Document 1 content", "Document 2 content"]],
            "metadatas": [[
                {
                    "type": "web_page",
                    "title": "About Alkemio",
                    "source": "https://alkem.io/about",
                },
                {
                    "type": "knowledge_base",
                    "title": "Platform Overview",
                    "source": "https://alkem.io/overview",
                },
            ]],
        },
        "source_scores": {
            "0": 8,
            "1": 5,
        },
    }


@pytest.fixture
def mock_graph_result_no_sources():
    """Graph result with no source scores."""
    return {
        "final_answer": "I cannot answer that question.",
        "knowledge_answer": "",
        "human_language": "en",
        "knowledge_language": "en",
        "knowledge_docs": {},
        "source_scores": {},
    }


@pytest.fixture
def mock_compiled_graph(mock_graph_result):
    """A mock compiled graph that returns realistic results."""
    graph = MagicMock()
    graph.invoke.return_value = mock_graph_result
    return graph
