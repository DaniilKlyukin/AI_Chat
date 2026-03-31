import os
import shutil
import uuid
import time
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile
from app.core.config import settings

class FileService:
    @staticmethod
    async def save_temp_file(file: UploadFile, session_id: str) -> Path:
        safe_name = f"{uuid.uuid4()}_{Path(file.filename).name}"
        temp_dir = settings.STORAGE_DIR / "temp" / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / safe_name
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    @staticmethod
    def get_file_content_safe(path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "[Ошибка чтения файла или бинарный формат]"

    @staticmethod
    def cleanup_old_data():
        now = time.time()
        temp_root = settings.STORAGE_DIR / "temp"
        if temp_root.exists():
            for session_dir in temp_root.iterdir():
                if now - session_dir.stat().st_mtime > 3600:
                    shutil.rmtree(session_dir)