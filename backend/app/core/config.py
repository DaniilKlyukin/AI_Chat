from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    MODEL: str = "ollama/deepseek-r1:8b"
    API_BASE: str = "http://localhost:11434"
    OLLAMA_API_KEY: str = "ollama"
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9

    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = BACKEND_DIR.parent
    FRONTEND_DIR: Path = ROOT_DIR / "frontend"
    SYSTEM_PROMPT_PATH: Path = ROOT_DIR / "system_prompt.txt"
    STORAGE_DIR: Path = BACKEND_DIR / "storage"

    class Config:
        env_file = ".env"

settings = Settings()
settings.STORAGE_DIR.mkdir(exist_ok=True)