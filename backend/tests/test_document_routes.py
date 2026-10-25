from types import SimpleNamespace

from fastapi.testclient import TestClient

import backend.api.routes as routes
import backend.database.db as db_module
from backend.database.db import replace_document, search_documents
from backend.llm.ollama_client import OllamaError
from backend.main import app


def isolate_database(monkeypatch, path):
    monkeypatch.setattr(
        db_module,
        "settings",
        SimpleNamespace(database_path=str(path)),
    )


def test_upload_document_falls_back_when_embeddings_fail(
    monkeypatch, tmp_path
):
    isolate_database(monkeypatch, tmp_path / "upload-test.db")

    class FakeOllamaClient:
        async def embed(self, texts):
            raise OllamaError("Embedding service unavailable")

    monkeypatch.setattr(routes, "OllamaClient", FakeOllamaClient)

    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
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
    isolate_database(monkeypatch, tmp_path / "query-test.db")

    class FakeOllamaClient:
        async def embed(self, texts):
            raise OllamaError("Embedding service unavailable")

        async def generate(self, prompt, system=None):
            assert "Python supports automated testing." in prompt
            return "The document says Python supports automated testing."

    monkeypatch.setattr(routes, "OllamaClient", FakeOllamaClient)

    with TestClient(app) as client:
        replace_document(
            "notes.txt",
            ["Python supports automated testing."],
        )

        response = client.post(
            "/api/documents/query",
            json={"text": "Explain automated testing"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "automated testing" in data["answer"]
    assert data["sources"]
    assert data["sources"][0]["name"] == "notes.txt"
