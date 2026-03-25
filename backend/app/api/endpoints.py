import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from app.services.file_service import FileService
from app.services.history_service import history_manager
from app.services.ai_service import ai_service
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.FRONTEND_DIR))

@router.get("/")
async def serve_index(request: Request):
    js_p = settings.FRONTEND_DIR / "script.js"
    css_p = settings.FRONTEND_DIR / "style.css"
    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "js_ver": os.path.getmtime(js_p) if js_p.exists() else 1,
        "css_ver": os.path.getmtime(css_p) if css_p.exists() else 1
    })

@router.post("/api/chat")
async def chat_endpoint(
        message: str = Form(...),
        session_id: str = Form(...),
        files: Optional[List[UploadFile]] = File(None)
):
    history_snapshot = history_manager.get_history(session_id)

    full_message = message
    if files:
        file_texts = []
        for f in files:
            if f.filename:
                text = await FileService.extract_text(f)
                file_texts.append(f"--- Содержимое файла {f.filename} ---\n{text}")
        if file_texts:
            full_message += "\n\n" + "\n\n".join(file_texts)

    history_manager.add_message(session_id, "user", full_message)

    ai_data = await ai_service.get_response(full_message, history_snapshot, session_id)
    response_text = ai_data["text"]

    history_manager.add_message(session_id, "assistant", response_text)

    download_url = FileService.create_session_zip(session_id)

    return {
        "status": "success",
        "response": response_text,
        "download_url": download_url
    }

@router.get("/api/chat/history")
async def get_chat_history(session_id: str):
    return {"status": "success", "history": history_manager.get_display_history(session_id)}

@router.post("/api/system/clear-history")
async def clear_chat_history(session_id: str):
    history_manager.clear(session_id)
    session_storage = settings.STORAGE_DIR / session_id
    if session_storage.exists():
        shutil.rmtree(session_storage)
    zip_file = settings.STORAGE_DIR / f"project_{session_id}.zip"
    if zip_file.exists():
        os.remove(zip_file)
    return {"status": "ok"}