
import asyncio
import json

from backend.agent.engine import AgentEngine


class FakeLLM:
    """Predictable mock model; no Ollama connection required."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    async def generate(
        self,
        prompt,
        system="You are a helpful assistant.",
        format=None,
    ):
        self.calls.append({"prompt": prompt, "format": format})
        return next(self.responses)


def test_agent_executes_calculator_and_returns_answer():
    async def scenario():
        llm = FakeLLM([
            json.dumps({
                "action": "tool",
                "tool": "calculator",
                "arguments": {"expression": "125 * 8"},
                "explanation": "Calculate the multiplication.",
            }),
            json.dumps({
                "action": "final",
                "answer": "1000",
                "explanation": "The calculator returned 1000.",
            }),
        ])

        result = await AgentEngine(llm=llm).run(
            "Calculate 125 multiplied by 8."
        )

        assert result["status"] == "completed"
        assert result["answer"] == "1000"
        assert result["trace"][0]["status"] == "success"
        assert result["trace"][0]["result_preview"] == "1000"
        assert llm.calls[0]["format"] == "json"

    asyncio.run(scenario())


def test_agent_rejects_invalid_action_schema():
    async def scenario():
        llm = FakeLLM([
            '{"action": "not_a_valid_action", "answer": "1000"}'
        ])

        result = await AgentEngine(llm=llm).run(
            "Calculate 125 multiplied by 8."
        )

        assert result["status"] == "invalid_action"
        assert result["trace"][0]["status"] == "rejected"

    asyncio.run(scenario())


def test_agent_stops_repeated_tool_calls():
    async def scenario():
        tool_action = json.dumps({
            "action": "tool",
            "tool": "calculator",
            "arguments": {"expression": "2 + 2"},
            "explanation": "Calculate two plus two.",
        })

        llm = FakeLLM([
            tool_action,
            tool_action,
            "The result is 4.",
        ])

        result = await AgentEngine(llm=llm).run("Calculate 2 + 2.")

        assert result["status"] == "completed"
        assert any(
            entry.get("reason") == "Duplicate tool call prevented"
            for entry in result["trace"]
        )

    asyncio.run(scenario())
