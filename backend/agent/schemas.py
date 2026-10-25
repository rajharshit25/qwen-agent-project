
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentAction(BaseModel):
    """
    Validated action returned by the agent's language model.

    Unexpected fields are rejected to catch malformed model responses.
    Tool allowlist enforcement remains in AgentEngine and the tool registry.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["tool", "final"]
    tool: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None
    explanation: str = ""

    @field_validator("tool")
    @classmethod
    def tool_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Tool name must not be blank")
        return value

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Answer must not be blank")
        return value
