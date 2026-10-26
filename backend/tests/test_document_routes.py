from dataclasses import replace
from types import SimpleNamespace

from fastapi.testclient import TestClient

import backend.api.routes as routes
import backend.database.db as db_module
import backend.main as main_module
from backend.config import settings
from backend.database.db import replace_document, search_documents
from backend.llm.ollama_client import OllamaError


TEST_API_KEY = "test-api-key"


def configure_test_api_key(monkeypatch):
    test_settings = replace(
        settings,
        qwen_agent_api_key=TEST_API_KEY,
    )
    monkeypatch.setattr(main_module, "settings", test_settings)


def isolate_database(monkeypatch, path):
    monkeypatch.setattr(
        db_module,
        "settings",
        SimpleNamespace(database_path=str(path)),
    )


def test_upload_document_falls_back_when_embeddings_fail(
    monkeypatch, tmp_path
):
    configure_test_api_key(monkeypatch)
    isolate_database(monkeypatch, tmp_path / "upload-test.db")

    class FakeOllamaClient:
        async def embed(self, texts):
            raise OllamaError("Embedding service unavailable")

    monkeypatch.setattr(routes, "OllamaClient", FakeOllamaClient)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/documents",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "name": "notes.txt",
                "text": "Python supports automated testing.",
            },
        )

    assert response.status_code == 200
    assert response.json()["stored_chunks"] == 1
    assert response.json()["method"] == (
        "SQLite lexical search (embedding unavailable)"
    )

    results = search_documents("automated testing")
    assert len(results) == 1
    assert results[0]["name"] == "notes.txt"


def test_document_query_falls_back_when_query_embedding_fails(
    monkeypatch, tmp_path
):
    configure_test_api_key(monkeypatch)
    isolate_database(monkeypatch, tmp_path / "query-test.db")

    class FakeOllamaClient:
        async def embed(self, texts):
            raise OllamaError("Embedding service unavailable")

        async def generate(self, prompt, system=None):
            assert "Python supports automated testing." in prompt
            return "The document says Python supports automated testing."

    monkeypatch.setattr(routes, "OllamaClient", FakeOllamaClient)

    with TestClient(main_module.app) as client:
        replace_document(
            "notes.txt",
            ["Python supports automated testing."],
        )

        response = client.post(
            "/api/documents/query",
            headers={"X-API-Key": TEST_API_KEY},
            json={"text": "Explain automated testing"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "automated testing" in data["answer"]
    assert data["sources"]
    assert data["sources"][0]["name"] == "notes.txt"