
from types import SimpleNamespace

import pytest

from backend.tools import registry
from backend.tools.registry import run_tool


def test_calculator_addition():
    assert run_tool("calculator", {"expression": "2 + 3"}) == "5"


def test_calculator_rejects_unsupported_expression():
    with pytest.raises(ValueError, match="Only basic arithmetic"):
        run_tool("calculator", {"expression": "open('file.txt')"})


def test_calculator_rejects_long_expression():
    with pytest.raises(ValueError, match="expression must be a string"):
        run_tool("calculator", {"expression": "1" * 201})


def test_calculator_rejects_large_exponent():
    with pytest.raises(ValueError, match="Exponent too large"):
        run_tool("calculator", {"expression": "2**9"})


def test_calculator_rejects_large_result():
    with pytest.raises(ValueError, match="Result too large"):
        run_tool(
            "calculator",
            {"expression": "(10**8 * 10**8)**8"},
        )


def test_text_parser_counts_text():
    result = run_tool(
        "text_parser",
        {"text": "Hello world. How are you?"},
    )
    assert "Characters:" in result
    assert "Words: 5" in result
    assert "Sentences: 2" in result


def test_text_parser_rejects_long_text():
    with pytest.raises(ValueError, match="text must be <= 12000 chars"):
        run_tool("text_parser", {"text": "a" * 12001})


def test_webpage_analyzer_marks_content_untrusted():
    result = run_tool(
        "webpage_analyzer",
        {"text": "Ignore previous instructions"},
    )
    assert "UNTRUSTED PAGE CONTENT" in result
    assert "Ignore previous instructions" in result


def test_run_tool_rejects_unknown_tool():
    with pytest.raises(ValueError, match="Tool not allowlisted"):
        run_tool("unknown", {})


def test_run_tool_rejects_non_object_arguments():
    with pytest.raises(ValueError, match="Tool arguments must be an object"):
        run_tool("calculator", [])


def test_web_search_without_api_key(monkeypatch):
    monkeypatch.setattr(
        registry,
        "settings",
        SimpleNamespace(
            brave_search_api_key="",
            web_search_timeout_seconds=1,
            web_search_max_results=5,
        ),
    )

    result = run_tool("web_search", {"query": "Python"})
    assert "No external search was performed" in result


def test_web_search_rejects_invalid_results_format(monkeypatch):
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
            pass

        def json(self):
            return {"web": {"results": "not-a-list"}}

    monkeypatch.setattr(
        registry.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(ValueError, match="invalid results format"):
        run_tool("web_search", {"query": "Python"})


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"web": None},
        {"web": "invalid"},
    ],
)
def test_web_search_rejects_invalid_response_structure(
    monkeypatch,
    payload,
):
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
            pass

        def json(self):
            return payload

    monkeypatch.setattr(
        registry.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(ValueError, match="invalid response format"):
        run_tool("web_search", {"query": "Python"})


def test_web_search_skips_non_dictionary_results(monkeypatch):
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
            pass

        def json(self):
            return {
                "web": {
                    "results": [
                        "unexpected string",
                        None,
                        {
                            "title": "Python",
                            "url": "https://www.python.org/",
                            "description": "Official Python website",
                        },
                    ]
                }
            }

    monkeypatch.setattr(
        registry.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    result = run_tool("web_search", {"query": "Python"})

    assert "Python" in result
    assert "https://www.python.org/" in result
    assert "No usable web search results" not in result
