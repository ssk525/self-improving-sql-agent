from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///data/store.db"
    groq_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    use_ollama: bool = False
    ollama_model: str = "llama3.2"
    mem0_api_key: str = ""
    agent_user_id: str = "demo_user"
    max_retries: int = 3
    statement_timeout_ms: int = 5000


settings = Settings()
