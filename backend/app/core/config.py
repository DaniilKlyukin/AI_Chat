from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    API_KEY: str = ""
    MODEL_FAST: str = "gemma-3-27b-it"
    MODEL_STRONG: str = "gemini-2.0-flash"

    COOLDOWN_FAST: int = 15
    COOLDOWN_STRONG: int = 180

    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ROOT_DIR: Path = BACKEND_DIR.parent
    FRONTEND_DIR: Path = ROOT_DIR / "frontend"
    SYSTEM_PROMPT_PATH: Path = ROOT_DIR / "system_prompt.txt"
    STORAGE_DIR: Path = BACKEND_DIR / "storage"
    DB_PATH: Path = BACKEND_DIR / "app.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
settings.STORAGE_DIR.mkdir(exist_ok=True)
(settings.STORAGE_DIR / "temp").mkdir(exist_ok=True)