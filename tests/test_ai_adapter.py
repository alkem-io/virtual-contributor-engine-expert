import pytest
from unittest.mock import patch, MagicMock
from alkemio_virtual_contributor_engine import Response

import ai_adapter


@pytest.mark.asyncio
async def test_invoke_happy_path(mock_input, mock_compiled_graph):
    """Test successful invocation returns response with sources."""
    mock_prompt_graph = MagicMock()
    mock_prompt_graph.compile.return_value = mock_compiled_graph

    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        result = await ai_adapter.invoke(mock_input)

    assert isinstance(result, Response)
    assert result.result == "Alkemio is a collaboration platform."
    assert result.human_language == "en"
    assert result.sources is not None
    assert len(result.sources) == 2
    assert result.sources[0].score == 8


@pytest.mark.asyncio
async def test_invoke_no_prompt_graph(mock_input_no_graph):
    """Test that missing prompt_graph returns error response."""
    result = await ai_adapter.invoke(mock_input_no_graph)

    assert isinstance(result, Response)
    assert "unavailable" in result.result.lower()


@pytest.mark.asyncio
async def test_invoke_graph_failure(mock_input):
    """Test that graph invocation failure returns error response."""
    mock_prompt_graph = MagicMock()
    mock_graph = MagicMock()
    mock_graph.stream.side_effect = RuntimeError("LLM API error")
    mock_prompt_graph.compile.return_value = mock_graph

    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        result = await ai_adapter.invoke(mock_input)

    assert isinstance(result, Response)
    assert "unavailable" in result.result.lower()


@pytest.mark.asyncio
async def test_invoke_no_sources(mock_input, mock_graph_result_no_sources):
    """Test invocation with no source scores."""
    mock_prompt_graph = MagicMock()
    mock_graph = MagicMock()
    mock_graph.stream.return_value = iter([{"answer": mock_graph_result_no_sources}])
    mock_prompt_graph.compile.return_value = mock_graph

    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        result = await ai_adapter.invoke(mock_input)

    assert isinstance(result, Response)
    assert result.result == "I cannot answer that question."
    assert result.sources == [] or not hasattr(result, "sources")


@pytest.mark.asyncio
async def test_invoke_filters_zero_score_sources(mock_input, mock_graph_result):
    """Test that sources with score 0 are filtered out."""
    mock_graph_result["source_scores"] = {"0": 8, "1": 0}
    mock_prompt_graph = MagicMock()
    mock_graph = MagicMock()
    mock_graph.stream.return_value = iter([
        {"retrieve": {
            "knowledge_docs": mock_graph_result.get("knowledge_docs", {}),
            "combined_knowledge_docs": "",
        }},
        {"answer": {k: v for k, v in mock_graph_result.items()
                    if k not in ("knowledge_docs", "combined_knowledge_docs")}},
    ])
    mock_prompt_graph.compile.return_value = mock_graph

    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        result = await ai_adapter.invoke(mock_input)

    assert len(result.sources) == 1
    assert result.sources[0].score == 8


def test_retrieve_function():
    """Test retrieve special node function."""
    mock_state = MagicMock()
    mock_state.rephrased_question = "What is Alkemio?"
    mock_state.bok_id = "bok-abc"

    mock_docs = {
        "ids": [["doc-1"]],
        "documents": [["content"]],
        "metadatas": [[{"type": "page", "title": "Test", "source": "http://test"}]],
    }

    with patch("ai_adapter.load_knowledge", return_value=mock_docs) as mock_load, \
         patch("ai_adapter.combine_query_results", return_value="combined") as mock_combine:
        result = ai_adapter.retrieve(mock_state)

    mock_load.assert_called_once_with("What is Alkemio?", "bok-abc")
    mock_combine.assert_called_once_with(mock_docs)
    assert result["knowledge_docs"] == mock_docs
    assert result["combined_knowledge_docs"] == "combined"


def test_retrieve_falls_back_to_first_message():
    """Test retrieve uses first message (newest) when no rephrased_question."""
    mock_state = MagicMock()
    mock_state.rephrased_question = None
    mock_state.messages = [
        MagicMock(content="current question"),
        MagicMock(content="older message"),
    ]
    mock_state.bok_id = "bok-abc"

    with patch("ai_adapter.load_knowledge", return_value={}) as mock_load, \
         patch("ai_adapter.combine_query_results", return_value=""):
        ai_adapter.retrieve(mock_state)

    mock_load.assert_called_once_with("current question", "bok-abc")


@pytest.mark.asyncio
async def test_invoke_passes_history_directly(mock_input, mock_compiled_graph):
    """Test that history is passed directly to the graph without modification."""
    mock_prompt_graph = MagicMock()
    mock_prompt_graph.compile.return_value = mock_compiled_graph

    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        await ai_adapter.invoke(mock_input)

    call_args = mock_compiled_graph.stream.call_args[0][0]
    messages = call_args["messages"]
    # History should be passed as-is (server already includes current message)
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi there!"


def test_source_title_formatting(mock_input, mock_graph_result):
    """Test that source titles are formatted correctly."""
    # CamelCase type should be split
    mock_graph_result["knowledge_docs"]["metadatas"][0][0]["type"] = "webPage"
    mock_prompt_graph = MagicMock()
    mock_graph = MagicMock()
    mock_graph.stream.return_value = iter([
        {"retrieve": {
            "knowledge_docs": mock_graph_result.get("knowledge_docs", {}),
            "combined_knowledge_docs": "",
        }},
        {"answer": {k: v for k, v in mock_graph_result.items()
                    if k not in ("knowledge_docs", "combined_knowledge_docs")}},
    ])
    mock_prompt_graph.compile.return_value = mock_graph

    import asyncio
    with patch.object(ai_adapter, "PromptGraph") as MockPG:
        MockPG.from_dict.return_value = mock_prompt_graph
        result = asyncio.get_event_loop().run_until_complete(
            ai_adapter.invoke(mock_input)
        )

    # webPage -> "Web page" via regex split
    assert "[Web page]" in result.sources[0].title
