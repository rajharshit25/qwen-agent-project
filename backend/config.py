import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    ollama_timeout: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    database_path: str = os.getenv("DATABASE_PATH", "data/agent.db")
    max_agent_steps: int = int(os.getenv("MAX_AGENT_STEPS", "5"))
    max_request_chars: int = int(os.getenv("MAX_REQUEST_CHARS", "12000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
settings = Settings()
