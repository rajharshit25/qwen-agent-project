from types import SimpleNamespace

import httpx
import pytest

import backend.tools.registry as registry
from backend.tools.registry import run_tool


def test_calculator():
    assert run_tool("calculator", {"expression": "(12+8)/4"}) == "5.0"


def test_reject_code():
    with pytest.raises((ValueError, SyntaxError)):
        run_tool("calculator", {"expression": "__import__('os').system('whoami')"})


def test_text_parser():
    result = run_tool(
        "text_parser",
        {"text": "Hello world. Another sentence!"},
    )
    assert "Words: 4" in result and "Sentences: 2" in result


def test_unknown_tool():
    with pytest.raises(ValueError):
        run_tool("shell", {})


def test_web_search_rejects_empty_query():
    with pytest.raises(ValueError, match="query"):
        run_tool("web_search", {"query": "  "})


def test_web_search_without_api_key_returns_friendly_message(monkeypatch):
    monkeypatch.setattr(
        registry,
        "settings",
        SimpleNamespace(
            brave_search_api_key="",
            web_search_timeout_seconds=8,
            web_search_max_results=5,
        ),
    )

    result = registry.web_search({"query": "Python"})
    assert "no search API key is configured" in result
    assert "No external search was performed" in result

def test_web_search_success_and_result_limit(monkeypatch):
    monkeypatch.setattr(
        registry,
        "settings",
        SimpleNamespace(
            brave_search_api_key="test-key",
            web_search_timeout_seconds=3,
            web_search_max_results=1,
        ),
    )

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "web": {
                    "results": [
                        {
                            "title": "First result",
                            "url": "https://example.com/1",
                            "description": "First snippet",
                        },
                        {
                            "title": "Second result",
                            "url": "https://example.com/2",
                            "description": "Second snippet",
                        },
                    ]
                }
            }

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(registry.httpx, "get", fake_get)

    result = run_tool("web_search", {"query": "Python tutorials"})

    assert "First result" in result
    assert "First snippet" in result
    assert "Second result" not in result
    assert captured["url"] == "https://api.search.brave.com/res/v1/web/search"
    assert captured["params"]["q"] == "Python tutorials"
    assert captured["params"]["count"] == 1
    assert captured["timeout"] == 3
    assert captured["headers"]["X-Subscription-Token"] == "test-key"


def test_web_search_timeout_is_propagated(monkeypatch):
    monkeypatch.setattr(
        registry,
        "settings",
        SimpleNamespace(
            brave_search_api_key="test-key",
            web_search_timeout_seconds=1,
            web_search_max_results=5,
        ),
    )

    def fake_get(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(registry.httpx, "get", fake_get)

    with pytest.raises(httpx.TimeoutException):
        run_tool("web_search", {"query": "Python"})


def test_web_search_provider_error_is_propagated(monkeypatch):
    monkeypatch.setattr(
        registry,
        "settings",
        SimpleNamespace(
            brave_search_api_key="test-key",
            web_search_timeout_seconds=1,
            web_search_max_results=5,
        ),
    )

    class FakeResponse:
        def raise_for_status(self):
            raise RuntimeError("provider failure")

    monkeypatch.setattr(
        registry.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(RuntimeError, match="provider failure"):
        run_tool("web_search", {"query": "Python"})
