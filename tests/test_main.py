import pytest
import sys
import logging
from unittest.mock import patch, AsyncMock
from alkemio_virtual_contributor_engine import Response


@pytest.fixture(autouse=True)
def _isolate_main():
    """Remove cached main module so each test gets a fresh import."""
    sys.modules.pop("main", None)
    yield
    sys.modules.pop("main", None)


def _import_main():
    """Import main.py with asyncio.run and engine patched out."""
    with patch("asyncio.run"):
        import main
    return main


async def test_on_request_calls_invoke(mock_input):
    """Test on_request calls ai_adapter.invoke and returns Response."""
    mock_response = Response(
        result="Test answer",
        original_result="Test answer",
        human_language="en",
        result_language="en",
        knowledge_language="en",
        sources=[],
    )

    main = _import_main()
    with patch.object(main.ai_adapter, "invoke",
                      new_callable=AsyncMock, return_value=mock_response):
        result = await main.on_request(mock_input)

    assert isinstance(result, Response)
    assert result.result == "Test answer"


async def test_on_request_logs_info(mock_input, caplog):
    """Test on_request logs persona ID and VC name at INFO."""
    mock_response = Response(
        result="Answer",
        original_result="Answer",
        human_language="en",
        sources=[],
    )

    main = _import_main()
    with patch.object(main.ai_adapter, "invoke",
                      new_callable=AsyncMock, return_value=mock_response):
        with caplog.at_level(logging.INFO):
            await main.on_request(mock_input)

    assert "persona-456" in caplog.text
    assert "Test VC" in caplog.text
    assert "What is Alkemio?" in caplog.text
