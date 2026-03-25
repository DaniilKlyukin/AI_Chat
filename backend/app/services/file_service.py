import io
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import pypdf
import docx
from app.core.config import settings

class FileService:
    @staticmethod
    async def extract_text(file: UploadFile) -> str:
        content = await file.read()
        ext = Path(file.filename).suffix.lower()

        if ext == '.pdf':
            try:
                reader = pypdf.PdfReader(io.BytesIO(content))
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text.strip()
            except:
                return "[Ошибка чтения PDF]"

        elif ext == '.docx':
            try:
                doc = docx.Document(io.BytesIO(content))
                return "\n".join([p.text for p in doc.paragraphs])
            except:
                return "[Ошибка чтения DOCX]"

        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('cp1251')
            except:
                return "[Ошибка: неподдерживаемая кодировка файла]"

    @staticmethod
    def create_session_zip(session_id: str) -> Optional[str]:
        session_storage = settings.STORAGE_DIR / session_id
        if session_storage.exists() and any(session_storage.iterdir()):
            zip_base_name = settings.STORAGE_DIR / f"project_{session_id}"
            shutil.make_archive(str(zip_base_name), 'zip', str(session_storage))
            return f"/storage/project_{session_id}.zip"
        return None