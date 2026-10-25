import asyncio

from backend.agent.engine import AgentEngine


class EmptyResponseLLM:
    async def generate(
        self,
        prompt,
        system="You are a helpful assistant.",
        format=None,
    ):
        return ""


def test_agent_returns_invalid_action_for_empty_model_response():
    async def scenario():
        result = await AgentEngine(llm=EmptyResponseLLM()).run(
            "Calculate 2 + 2."
        )

        assert result["status"] == "invalid_action"
        assert result["trace"][0]["status"] == "rejected"
        assert result["trace"][0]["reason"] == "Invalid action schema"

    asyncio.run(scenario())


class PlainTextResponseLLM:
    async def generate(
        self,
        prompt,
        system="You are a helpful assistant.",
        format=None,
    ):
        return "I will calculate that now, but here is no JSON."


def test_agent_rejects_plain_text_model_response():
    async def scenario():
        result = await AgentEngine(llm=PlainTextResponseLLM()).run(
            "Calculate 2 + 2."
        )

        assert result["status"] == "invalid_action"
        assert result["trace"][0]["status"] == "rejected"
        assert result["trace"][0]["reason"] == "Invalid action schema"

    asyncio.run(scenario())


class IncompleteJSONResponseLLM:
    async def generate(
        self,
        prompt,
        system="You are a helpful assistant.",
        format=None,
    ):
        return '{"action": "tool", "tool":'


def test_agent_rejects_incomplete_json_model_response():
    async def scenario():
        result = await AgentEngine(llm=IncompleteJSONResponseLLM()).run(
            "Calculate 2 + 2."
        )

        assert result["status"] == "invalid_action"
        assert result["trace"][0]["status"] == "rejected"
        assert result["trace"][0]["reason"] == "Invalid action schema"

    asyncio.run(scenario())
