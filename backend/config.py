
import os
from dataclasses import dataclass
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

    def __post_init__(self):
        if not self.ollama_base_url.strip():
            raise ValueError("OLLAMA_BASE_URL must not be empty")

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


settings = Settings()
