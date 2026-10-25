from fastapi.testclient import TestClient

from backend.main import app


def test_agent_rejects_goal_over_12000_characters():
    with TestClient(app) as client:
        response = client.post(
            "/api/agent",
            json={"goal": "a" * 12001},
        )

    assert response.status_code == 422


def test_agent_rejects_page_text_over_12000_characters():
    with TestClient(app) as client:
        response = client.post(
            "/api/agent",
            json={
                "goal": "Summarize this page",
                "page_text": "a" * 12001,
            },
        )

    assert response.status_code == 422
