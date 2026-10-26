from dataclasses import replace

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.config import settings


TEST_API_KEY = "test-api-key"


def configure_test_api_key(monkeypatch):
    test_settings = replace(
        settings,
        qwen_agent_api_key=TEST_API_KEY,
    )
    monkeypatch.setattr(main_module, "settings", test_settings)


def test_agent_rejects_goal_over_12000_characters(monkeypatch):
    configure_test_api_key(monkeypatch)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/agent",
            headers={"X-API-Key": TEST_API_KEY},
            json={"goal": "a" * 12001},
        )

    assert response.status_code == 422


def test_agent_rejects_page_text_over_12000_characters(monkeypatch):
    configure_test_api_key(monkeypatch)

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/agent",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "goal": "Summarize this page",
                "page_text": "a" * 12001,
            },
        )

    assert response.status_code == 422