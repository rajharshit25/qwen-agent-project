import os
from dataclasses import dataclass
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    )
    ollama_model: str = os.getenv(
        "OLLAMA_MODEL", "qwen2.5:1.5b"
    )
    ollama_timeout: float = float(
        os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")
    )
    database_path: str = os.getenv(
        "DATABASE_PATH", "data/agent.db"
    )
    max_agent_steps: int = int(
        os.getenv("MAX_AGENT_STEPS", "5")
    )
    max_request_chars: int = int(
        os.getenv("MAX_REQUEST_CHARS", "12000")
    )
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    brave_search_api_key: str = os.getenv("BRAVE_SEARCH_API_KEY", "")
    web_search_timeout_seconds: float = float(
        os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "8")
    )
    web_search_max_results: int = int(
        os.getenv("WEB_SEARCH_MAX_RESULTS", "5")
    )

    def __post_init__(self):
        try:
            parsed_url = urlparse(self.ollama_base_url.strip())
            port = parsed_url.port
        except ValueError as exc:
            raise ValueError(
                "OLLAMA_BASE_URL must contain a valid port"
            ) from exc

        if (
            parsed_url.scheme not in ("http", "https")
            or not parsed_url.hostname
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.query
            or parsed_url.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError(
                "OLLAMA_BASE_URL must be a valid HTTP(S) URL without credentials, query, or fragment"
            )

        if not self.ollama_model.strip():
            raise ValueError("OLLAMA_MODEL must not be empty")

        if self.ollama_timeout <= 0:
            raise ValueError("OLLAMA_TIMEOUT_SECONDS must be greater than 0")

        if self.max_agent_steps < 1:
            raise ValueError("MAX_AGENT_STEPS must be at least 1")

        if self.max_request_chars < 1:
            raise ValueError("MAX_REQUEST_CHARS must be at least 1")

        if not self.database_path.strip():
            raise ValueError("DATABASE_PATH must not be empty")

        if self.web_search_timeout_seconds <= 0:
            raise ValueError(
                "WEB_SEARCH_TIMEOUT_SECONDS must be greater than 0"
            )

        if not 1 <= self.web_search_max_results <= 10:
            raise ValueError(
                "WEB_SEARCH_MAX_RESULTS must be between 1 and 10"
            )


settings = Settings()
