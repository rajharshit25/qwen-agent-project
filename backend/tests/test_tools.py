import pytest
from backend.tools.registry import run_tool

def test_calculator():
    assert run_tool("calculator",{"expression":"(12+8)/4"}) == "5.0"

def test_reject_code():
    with pytest.raises((ValueError,SyntaxError)):
        run_tool("calculator",{"expression":"__import__('os').system('whoami')"})

def test_text_parser():
    result=run_tool("text_parser",{"text":"Hello world. Another sentence!"})
    assert "Words: 4" in result and "Sentences: 2" in result

def test_unknown_tool():
    with pytest.raises(ValueError): run_tool("shell",{})
