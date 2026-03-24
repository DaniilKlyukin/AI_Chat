from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    MODEL: str = "ollama/qwen3:8b"
    API_BASE: str = "http://localhost:11434"
    OLLAMA_API_KEY: Optional[str] = None

    class Config:
        env_file = ROOT_DIR / ".env"
        env_file_encoding = 'utf-8'

settings = Settings()