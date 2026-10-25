
import json
import math

import httpx

from backend.config import settings


class OllamaError(RuntimeError):
    """Raised when an Ollama request fails or returns invalid data."""


class OllamaClient:
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout

    async def generate(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        format: str | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }

        if format is not None:
            payload["format"] = format

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            result = data.get("response") if isinstance(data, dict) else None

            if not isinstance(result, str):
                raise OllamaError(
                    "Ollama returned an unexpected response."
                )

            return result.strip()

        except httpx.HTTPError as exc:
            raise OllamaError(
                f"Cannot reach Ollama/model '{self.model}': {exc}"
            ) from exc
        except ValueError as exc:
            raise OllamaError(
                "Ollama returned invalid JSON."
            ) from exc

    async def chat(self, messages: list[dict]) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
                response.raise_for_status()
                data = response.json()

            if not isinstance(data, dict):
                raise OllamaError(
                    "Ollama returned an unexpected chat response."
                )

            message = data.get("message")
            if not isinstance(message, dict):
                raise OllamaError(
                    "Ollama returned an invalid chat message."
                )

            content = message.get("content")
            if not isinstance(content, str):
                raise OllamaError(
                    "Ollama returned invalid chat content."
                )

            return content.strip()

        except httpx.HTTPError as exc:
            raise OllamaError(
                f"Ollama chat request failed: {exc}"
            ) from exc
        except ValueError as exc:
            raise OllamaError(
                "Ollama returned invalid chat JSON."
            ) from exc

    async def stream_chat(self, messages: list[dict]):
        """Yield text chunks from Ollama's streaming chat API."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise OllamaError(
                                "Ollama returned invalid streaming JSON."
                            ) from exc

                        if not isinstance(data, dict):
                            raise OllamaError(
                                "Ollama returned an unexpected "
                                "streaming response."
                            )

                        if data.get("error"):
                            raise OllamaError(str(data["error"]))

                        message = data.get("message", {})
                        if not isinstance(message, dict):
                            raise OllamaError(
                                "Ollama returned an invalid message chunk."
                            )

                        content = message.get("content", "")
                        if not isinstance(content, str):
                            raise OllamaError(
                                "Ollama returned invalid text content."
                            )

                        if content:
                            yield content

                        if data.get("done") is True:
                            return

        except httpx.HTTPError as exc:
            raise OllamaError(
                f"Ollama streaming chat request failed: {exc}"
            ) from exc

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Create local embeddings using the configured Ollama model."""
        if not isinstance(texts, list) or not texts:
            raise OllamaError(
                "Embedding input must be a non-empty list."
            )

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise OllamaError(
                "Embedding inputs must be non-empty strings."
            )

        payload = {
            "model": settings.embedding_model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(
                f"Ollama embedding request failed: {exc}"
            ) from exc

        embeddings = (
            data.get("embeddings")
            if isinstance(data, dict)
            else None
        )

        if (
            not isinstance(embeddings, list)
            or len(embeddings) != len(texts)
        ):
            raise OllamaError(
                "Ollama returned an unexpected embeddings response."
            )

        validated = []

        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise OllamaError(
                    "Ollama returned an invalid embedding vector."
                )

            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            ):
                raise OllamaError(
                    "Ollama returned non-numeric embedding values."
                )

            validated.append([float(value) for value in vector])

        dimensions = {len(vector) for vector in validated}

        if len(dimensions) != 1:
            raise OllamaError(
                "Ollama returned inconsistent embedding dimensions."
            )

        return validated
