import httpx
from backend.config import settings

class OllamaError(RuntimeError):
    pass

class OllamaClient:
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout

    async def generate(self, prompt: str, system: str = "You are a helpful assistant.", format: str | None = None) -> str:
        payload = {"model": self.model, "system": system, "prompt": prompt, "stream": False,
                   "options": {"temperature": 0.2}}
        if format is not None:
            payload["format"] = format
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json().get("response")
                if not isinstance(result, str):
                    raise OllamaError("Ollama returned an unexpected response.")
                return result.strip()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Cannot reach Ollama/model '{self.model}': {exc}") from exc

    async def chat(self, messages: list[dict]) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat",
                    json={"model": self.model, "messages": messages, "stream": False,
                          "options": {"temperature": 0.2}})
                response.raise_for_status()
                return response.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            raise OllamaError(f"Ollama chat request failed: {exc}") from exc
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Create local embeddings using the configured Ollama embedding model."""
        import math

        if not isinstance(texts, list) or not texts:
            raise OllamaError("Embedding input must be a non-empty list.")

        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise OllamaError("Embedding inputs must be non-empty strings.")

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

        embeddings = data.get("embeddings") if isinstance(data, dict) else None

        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Ollama returned an unexpected embeddings response.")

        validated = []
        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise OllamaError("Ollama returned an invalid embedding vector.")

            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            ):
                raise OllamaError("Ollama returned non-numeric embedding values.")

            validated.append([float(value) for value in vector])

        dimensions = {len(vector) for vector in validated}
        if len(dimensions) != 1:
            raise OllamaError("Ollama returned inconsistent embedding dimensions.")

        return validated
