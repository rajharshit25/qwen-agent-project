
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

        assert sum(
            entry.get("status") == "success"
            and entry.get("tool") == "calculator"
            for entry in result["trace"]
        ) == 1

        assert result["status"] == "completed"
        assert len(llm.calls) == 3
        assert result["answer"] == "The result is 4."
        assert any(
            entry.get("reason") == "Duplicate tool call prevented"
            for entry in result["trace"]
        )

    asyncio.run(scenario())


def test_agent_can_use_two_different_tools():
    async def scenario():
        llm = FakeLLM([
            json.dumps({
                "action": "tool",
                "tool": "calculator",
                "arguments": {"expression": "2 + 2"},
                "explanation": "Calculate the result.",
            }),
            json.dumps({
                "action": "tool",
                "arguments": {"text": "four is the answer"},
                "tool": "text_parser",
                "explanation": "Count the words in the supplied text.",
            }),
            json.dumps({
                "action": "final",
                "answer": "The calculation is 4, and the text contains 4 words.",
                "explanation": "Both tool results are available.",
            }),
        ])

        result = await AgentEngine(llm=llm).run(
            "Calculate 2 + 2, then count the words in 'four is the answer'."
        )

        assert result["status"] == "completed"
        assert result["answer"] == (
            "The calculation is 4, and the text contains 4 words."
        )
        assert [
            entry["tool"]
            for entry in result["trace"]
            if entry.get("status") == "success"
        ] == ["calculator", "text_parser"]

    asyncio.run(scenario())


def test_agent_stops_at_configured_step_limit():
    async def scenario():
        first_action = json.dumps({
            "action": "tool",
            "tool": "calculator",
            "arguments": {"expression": "2 + 2"},
            "explanation": "Calculate the result.",
        })

        second_action = json.dumps({
            "action": "tool",
            "tool": "text_parser",
            "arguments": {"text": "hello world"},
            "explanation": "Count the words.",
        })

        llm = FakeLLM([
            first_action,
            second_action,
            "I completed two tool steps, but the task may need more work.",
        ])

        result = await AgentEngine(llm=llm, max_steps=2).run(
            "Calculate 2 + 2 and count the words in hello world."
        )

        assert result["status"] == "step_limit"
        assert len(result["trace"]) == 2
        assert len(llm.calls) == 3

    asyncio.run(scenario())

def test_agent_continues_after_tool_execution_error(monkeypatch):
    import backend.agent.engine as engine_module

    async def scenario():
        first_action = json.dumps({
            "action": "tool",
            "tool": "calculator",
            "arguments": {"expression": "2 + 2"},
            "explanation": "Calculate the result.",
        })

        second_action = json.dumps({
            "action": "tool",
            "tool": "text_parser",
            "arguments": {"text": "hello world"},
            "explanation": "Count the words.",
        })

        final_action = json.dumps({
            "action": "final",
            "answer": "The calculator failed, but the text contains two words.",
            "explanation": "Report the available evidence.",
        })

        llm = FakeLLM([first_action, second_action, final_action])

        def fake_run_tool(tool_name, arguments):
            if tool_name == "calculator":
                raise RuntimeError("Simulated calculator failure")
            if tool_name == "text_parser":
                return "Word count: 2"
            raise AssertionError(f"Unexpected tool: {tool_name}")

        monkeypatch.setattr(engine_module, "run_tool", fake_run_tool)

        result = await AgentEngine(llm=llm).run(
            "Calculate 2 + 2 and count the words in hello world."
        )

        assert result["status"] == "completed"
        assert "calculator failed" in result["answer"].lower()
        assert any(
            entry.get("tool") == "calculator"
            and entry.get("status") == "error"
            for entry in result["trace"]
        )
        assert any(
            entry.get("tool") == "text_parser"
            and entry.get("status") == "success"
            for entry in result["trace"]
        )

    asyncio.run(scenario())

