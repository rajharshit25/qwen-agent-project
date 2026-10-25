import asyncio
import httpx
import pytest

from backend.llm.ollama_client import OllamaClient, OllamaError


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeAsyncClient:
    response_data = None
    request_payload = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json):
        type(self).request_payload = {"url": url, "json": json}
        return FakeResponse(type(self).response_data)


def test_embed_returns_float_vectors_and_uses_embedding_model(monkeypatch):
    FakeAsyncClient.response_data = {
        "embeddings": [[1, 2.5], [3, 4]]
    }
    monkeypatch.setattr(
        "backend.llm.ollama_client.httpx.AsyncClient", FakeAsyncClient
    )
    monkeypatch.setattr(
        "backend.llm.ollama_client.settings",
        type(
            "TestSettings",
            (),
            {
                "embedding_model": "test-embed-model",
                "ollama_model": "test-chat-model",
                "ollama_base_url": "http://127.0.0.1:11434",
                "ollama_timeout": 10.0,
            },
        )(),
    )

    vectors = asyncio.run(OllamaClient(base_url="http://localhost:11434").embed(
        ["first text", "second text"]
    ))

    assert vectors == [[1.0, 2.5], [3.0, 4.0]]
    assert FakeAsyncClient.request_payload["url"] == (
        "http://localhost:11434/api/embed"
    )
    assert FakeAsyncClient.request_payload["json"] == {
        "model": "test-embed-model",
        "input": ["first text", "second text"],
    }


@pytest.mark.parametrize("texts", [[], [" "], ["valid", ""] , [None]])
def test_embed_rejects_empty_or_invalid_inputs(texts):
    with pytest.raises(OllamaError):
        asyncio.run(OllamaClient().embed(texts))


@pytest.mark.parametrize(
    "response_data",
    [
        {},
        {"embeddings": "not-a-list"},
        {"embeddings": [[1.0]]},
        {"embeddings": [[], [1.0]]},
        {"embeddings": [[1.0], [1.0, 2.0]]},
        {"embeddings": [[True]]},
        {"embeddings": [[float("nan")]]},
        {"embeddings": [[float("inf")]]},
        {"embeddings": [["invalid"]]},
    ],
)
def test_embed_rejects_malformed_vectors(monkeypatch, response_data):
    FakeAsyncClient.response_data = response_data
    monkeypatch.setattr(
        "backend.llm.ollama_client.httpx.AsyncClient", FakeAsyncClient
    )

    with pytest.raises(OllamaError):
        asyncio.run(OllamaClient().embed(["first", "second"]))
