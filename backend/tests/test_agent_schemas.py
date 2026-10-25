
import pytest
from pydantic import ValidationError

from backend.agent.schemas import AgentAction


def test_agent_action_rejects_blank_tool_name():
    with pytest.raises(ValidationError, match="Tool name must not be blank"):
        AgentAction(action="tool", tool="   ")


def test_agent_action_rejects_blank_answer():
    with pytest.raises(ValidationError, match="Answer must not be blank"):
        AgentAction(action="final", answer="   ")


def test_agent_action_rejects_unexpected_fields():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentAction(action="final", answer="Done", unexpected="value")


def test_agent_action_accepts_valid_tool_action():
    action = AgentAction(
        action="tool",
        tool="calculator",
        arguments={"expression": "2 + 2"},
    )

    assert action.tool == "calculator"
    assert action.arguments == {"expression": "2 + 2"}


def test_agent_action_accepts_valid_final_action():
    action = AgentAction(action="final", answer="Done")

    assert action.answer == "Done"
