
import json

from fastapi.testclient import TestClient

import backend.api.routes as routes
from backend.main import app


class FakeStreamingClient:
    async def stream_chat(self, messages):
        yield "Hello"
        yield " there!"

class FailingStreamingClient:
    async def stream_chat(self, messages):
        yield "Partial answer"
        raise routes.OllamaError("Simulated Ollama failure")


def test_stream_chat_emits_tokens_and_done_event(monkeypatch):
    saved_messages = []

    monkeypatch.setattr(
        routes,
        "OllamaClient",
        FakeStreamingClient,
    )
    monkeypatch.setattr(
        routes,
        "get_history",
        lambda session_id: [],
    )
    monkeypatch.setattr(
        routes,
        "add_message",
        lambda sid, role, content: saved_messages.append(
            (sid, role, content)
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/stream",
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
    saved_messages = []

    monkeypatch.setattr(
        routes,
        "OllamaClient",
        FailingStreamingClient,
    )
    monkeypatch.setattr(
        routes,
        "get_history",
        lambda session_id: [],
    )
    monkeypatch.setattr(
        routes,
        "add_message",
        lambda sid, role, content: saved_messages.append(
            (sid, role, content)
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/stream",
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


def test_stream_chat_rejects_blank_message():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat/stream",
            json={"message": "   "},
        )

    assert response.status_code == 422
