
import pytest

from backend.config import Settings


def test_valid_settings_are_accepted():
    config = Settings()
    assert config.ollama_model == "qwen2.5:1.5b"
    assert config.ollama_timeout > 0
    assert config.max_agent_steps >= 1
    assert config.max_request_chars >= 1


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("ollama_base_url", "   ", "OLLAMA_BASE_URL"),
        ("ollama_base_url", "file:///tmp/model", "OLLAMA_BASE_URL"),
        ("ollama_base_url", "ftp://localhost:11434", "OLLAMA_BASE_URL"),
        ("ollama_base_url", "http://", "OLLAMA_BASE_URL"),
        ("ollama_base_url", "http://localhost:99999", "OLLAMA_BASE_URL"),
        ("ollama_model", "", "OLLAMA_MODEL"),
        ("ollama_timeout", 0, "OLLAMA_TIMEOUT_SECONDS"),
        ("ollama_timeout", -1, "OLLAMA_TIMEOUT_SECONDS"),
        ("max_agent_steps", 0, "MAX_AGENT_STEPS"),
        ("max_agent_steps", -1, "MAX_AGENT_STEPS"),
        ("max_request_chars", 0, "MAX_REQUEST_CHARS"),
        ("max_request_chars", -1, "MAX_REQUEST_CHARS"),
        ("database_path", " ", "DATABASE_PATH"),
    ],
)
def test_invalid_settings_are_rejected(field, value, message):
    with pytest.raises(ValueError, match=message):
        Settings(**{field: value})
