import importlib
from unittest.mock import patch
import pytest


def _reload_config_with_env(mp, env):
    """Helper to reload config with specific env vars, bypassing .env file."""
    for key in ["LOG_LEVEL", "HISTORY_LENGTH", "RABBITMQ_HOST", "RABBITMQ_USER",
                "RABBITMQ_PASSWORD", "RABBITMQ_QUEUE", "RABBITMQ_RESULT_QUEUE",
                "VECTOR_DB_HOST", "VECTOR_DB_PORT", "MISTRAL_API_KEY",
                "EMBEDDINGS_API_KEY", "EMBEDDINGS_ENDPOINT"]:
        mp.delenv(key, raising=False)
    for k, v in env.items():
        mp.setenv(k, v)
    # Prevent load_dotenv from overriding our env vars
    with patch("dotenv.load_dotenv"):
        import config
        importlib.reload(config)
    return config


def test_log_level_valid_values():
    """Test that config accepts valid LOG_LEVEL values."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        with pytest.MonkeyPatch.context() as mp:
            cfg = _reload_config_with_env(mp, {"LOG_LEVEL": level})
            assert cfg.LOG_LEVEL == level


def test_log_level_invalid_value():
    """Test that config rejects invalid LOG_LEVEL values."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("LOG_LEVEL", "INVALID")
        import config
        with pytest.raises(AssertionError):
            importlib.reload(config)


def test_history_length_default():
    """Test that HISTORY_LENGTH defaults to 10 when not set."""
    with pytest.MonkeyPatch.context() as mp:
        cfg = _reload_config_with_env(mp, {"LOG_LEVEL": "INFO"})
        assert cfg.config["history_length"] == 10


def test_history_length_custom():
    """Test that HISTORY_LENGTH can be overridden."""
    with pytest.MonkeyPatch.context() as mp:
        cfg = _reload_config_with_env(mp, {
            "LOG_LEVEL": "INFO",
            "HISTORY_LENGTH": "20",
        })
        assert cfg.config["history_length"] == 20
