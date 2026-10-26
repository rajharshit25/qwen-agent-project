
import json
from dataclasses import replace

from fastapi.testclient import TestClient

import backend.api.routes as routes
import backend.main as main_module
from backend.config import settings


TEST_API_KEY = "test-api-key"


class FakeStreamingClient:
    async def stream_chat(self, messages):
        yield "Hello"
        yield " there!"


class FailingStreamingClient:
    async def stream_chat(self, messages):
        yield "Partial answer"
        raise routes.OllamaError("Simulated Ollama failure")


def configure_test_api_key(monkeypatch):
    test_settings = replace(
        settings,
        qwen_agent_api_key=TEST_API_KEY,
    )
    monkeypatch.setattr(main_module, "settings", test_settings)


def test_stream_chat_emits_tokens_and_done_event(monkeypatch):
    configure_test_api_key(monkeypatch)
    saved_messages = []

    monkeypatch.setattr(routes, "OllamaClient", FakeStreamingClient)
    monkeypatch.setattr(routes, "get_history", lambda session_id: [])
    monkeypatch.setattr(
        routes,
        "add_message",
        lambda sid, role, content: saved_messages.append(
            (sid, role, content)
        ),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/chat/stream",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "message": "Say hello",
                "session_id": "stream-test",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )

    body = response.text
    assert "event: token" in body
    assert '"text": "Hello"' in body
    assert '"text": " there!"' in body
    assert "event: done" in body

    done_event = body.split("event: done\n", 1)[1]
    done_data = done_event.split("data: ", 1)[1].split("\n", 1)[0]
    assert json.loads(done_data)["session_id"] == "stream-test"

    assert saved_messages == [
        ("stream-test", "user", "Say hello"),
        ("stream-test", "assistant", "Hello there!"),
    ]


def test_stream_chat_emits_error_when_ollama_fails(monkeypatch):
    configure_test_api_key(monkeypatch)
    saved_messages = []

    monkeypatch.setattr(
        routes,
        "OllamaClient",
        FailingStreamingClient,
    )
    monkeypatch.setattr(routes, "get_history", lambda session_id: [])
    monkeypatch.setattr(
        routes,
        "add_message",
        lambda sid, role, content: saved_messages.append(
            (sid, role, content)
        ),
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/chat/stream",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "message": "Test failure",
                "session_id": "stream-error-test",
            },
        )

    assert response.status_code == 200
    assert "event: token" in response.text
    assert "Partial answer" in response.text
    assert "event: error" in response.text
    assert "Simulated Ollama failure" in response.text

    # A failed stream must not save an incomplete conversation.
    assert saved_messages == []


def test_stream_chat_rejects_blank_message(monkeypatch):
    configure_test_api_key(monkeypatch)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/chat/stream",
            headers={"X-API-Key": TEST_API_KEY},
            json={"message": "   "},
        )

    assert response.status_code == 422
