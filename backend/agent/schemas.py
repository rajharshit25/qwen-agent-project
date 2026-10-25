from typing import Literal, Any
from pydantic import BaseModel, Field

class AgentAction(BaseModel):
    action: Literal["tool", "final"]
    tool: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None
    explanation: str = ""
