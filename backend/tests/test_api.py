from dataclasses import replace

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from backend.api.routes import ChatRequest
import backend.api.routes as routes
import backend.main as main_module
from backend.config import settings


TEST_API_KEY = "test-api-key"


def configure_test_api_key(monkeypatch):
    test_settings = replace(
        settings,
        qwen_agent_api_key=TEST_API_KEY,
    )
    monkeypatch.setattr(main_module, "settings", test_settings)


def test_chat_request_accepts_valid_session_id():
    request = ChatRequest(message="Hello", session_id="session-123")
    assert request.session_id == "session-123"


def test_chat_request_rejects_session_id_over_200_characters():
    with pytest.raises(ValidationError):
        ChatRequest(message="Hello", session_id="s" * 201)


def test_chat_request_rejects_whitespace_only_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_document_request_rejects_whitespace_only_name():
    from backend.api.routes import DocumentRequest

    with pytest.raises(ValidationError):
        DocumentRequest(name="   ", text="Some document text")


def test_chat_request_rejects_message_over_12000_characters():
    with pytest.raises(ValidationError):
        ChatRequest(message="a" * 12001)


def test_document_request_rejects_text_over_100000_characters():
    from backend.api.routes import DocumentRequest

    with pytest.raises(ValidationError):
        DocumentRequest(name="notes.txt", text="a" * 100001)


def test_agent_returns_503_when_model_generation_fails(monkeypatch):
    configure_test_api_key(monkeypatch)

    class FailingAgent:
        async def run(self, goal, page_text=""):
            return {
                "answer": (
                    "I couldn't complete the request because "
                    "the AI model encountered an error. "
                    "Please check that Ollama is running and try again."
                ),
                "trace": [
                    {
                        "step": 1,
                        "status": "error",
                        "reason": "Model response generation failed",
                    }
                ],
                "status": "llm_error",
            }

    monkeypatch.setattr(routes, "AgentEngine", FailingAgent)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/agent",
            headers={"X-API-Key": TEST_API_KEY},
            json={"goal": "Calculate 2 + 2."},
        )

    assert response.status_code == 503
    assert response.json()["status"] == "llm_error"
    assert "trace" in response.json()