from pydantic import ValidationError
import pytest

from backend.api.routes import ChatRequest


def test_chat_request_accepts_valid_session_id():
    request = ChatRequest(message="Hello", session_id="session-123")
    assert request.session_id == "session-123"


def test_chat_request_rejects_session_id_over_200_characters():
    with pytest.raises(ValidationError):
        ChatRequest(message="Hello", session_id="s" * 201)
