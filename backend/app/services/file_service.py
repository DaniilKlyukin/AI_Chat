import io
from pathlib import Path
from fastapi import UploadFile
import pypdf
import docx

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
            except: return "[Ошибка чтения PDF]"

        elif ext == '.docx':
            try:
                doc = docx.Document(io.BytesIO(content))
                return "\n".join([p.text for p in doc.paragraphs])
            except: return "[Ошибка чтения DOCX]"

        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('cp1251')
            except:
                return "[Ошибка: неподдерживаемая кодировка файла]"