import logging
from unittest.mock import patch
from utils import load_knowledge, log_docs


def test_load_knowledge_calls_query_documents():
    """Test load_knowledge calls query_documents with correct params."""
    mock_docs = {
        "ids": [["doc-1"]],
        "documents": [["content"]],
        "metadatas": [[{"type": "page", "title": "Test", "source": "http://test"}]],
    }
    with patch("utils.query_documents", return_value=mock_docs) as mock_query:
        result = load_knowledge("test query", "bok-123")

    mock_query.assert_called_once_with("test query", "bok-123-knowledge", num_docs=4)
    assert result == mock_docs


def test_load_knowledge_empty_result():
    """Test load_knowledge handles empty results."""
    with patch("utils.query_documents", return_value={}):
        result = load_knowledge("query", "bok-empty")

    assert result == {}


def test_log_docs_with_valid_docs(caplog):
    """Test log_docs logs IDs at INFO level."""
    docs = {
        "ids": [["id-1", "id-2"]],
        "documents": [["doc1", "doc2"]],
    }
    with caplog.at_level(logging.INFO):
        log_docs(docs, "Knowledge")

    assert "Knowledge documents with ids [id-1,id-2] selected" in caplog.text


def test_log_docs_with_debug_details(caplog):
    """Test log_docs logs full docs at DEBUG level."""
    docs = {
        "ids": [["id-1"]],
        "documents": [["doc content"]],
    }
    with caplog.at_level(logging.DEBUG):
        log_docs(docs, "Test")

    assert "Test documents:" in caplog.text


def test_log_docs_empty_docs(caplog):
    """Test log_docs handles empty docs without crashing."""
    with caplog.at_level(logging.INFO):
        log_docs({}, "Empty")
    # Should not crash and should not log anything
    assert "Empty documents" not in caplog.text


def test_log_docs_none_docs(caplog):
    """Test log_docs handles None without crashing."""
    with caplog.at_level(logging.INFO):
        log_docs(None, "None")
    assert "None documents" not in caplog.text


def test_log_docs_empty_ids(caplog):
    """Test log_docs handles empty ids list."""
    docs = {"ids": [[]], "documents": [[]]}
    with caplog.at_level(logging.INFO):
        log_docs(docs, "EmptyIds")
    assert "EmptyIds documents" not in caplog.text
