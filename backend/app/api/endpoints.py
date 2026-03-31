import os
from fastapi import APIRouter, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from typing import List
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
        "css_ver": os.path.getmtime(css_p) if css_p.exists() else 1,
        "model_fast": settings.MODEL_FAST,
        "model_strong": settings.MODEL_STRONG
    })

@router.post("/api/chat")
async def chat_endpoint(
        background_tasks: BackgroundTasks,
        message: str = Form(...),
        session_id: str = Form(...),
        model_id: str = Form(...),
        files: List[UploadFile] = File(None)
):
    background_tasks.add_task(FileService.cleanup_old_data)

    history_snapshot = history_manager.get_history(session_id)
    saved_paths = []
    if files:
        for f in files:
            if f.filename:
                path = await FileService.save_temp_file(f, session_id)
                saved_paths.append(str(path))

    ai_data = await ai_service.get_response(message, history_snapshot, session_id, model_id, saved_paths)

    if "ЛИМИТ:" not in ai_data["text"]:
        history_manager.add_message(session_id, "user", message)
        history_manager.add_message(session_id, "assistant", ai_data["text"])

    for p in saved_paths:
        if os.path.exists(p): os.remove(p)

    return {
        "status": "success",
        "response": ai_data["text"],
        "model_used": ai_data["model"]
    }

@router.get("/api/chat/history")
async def get_chat_history(session_id: str):
    return {"status": "success", "history": history_manager.get_display_history(session_id)}

@router.post("/api/system/clear-history")
async def clear_chat_history(session_id: str):
    history_manager.clear(session_id)
    return {"status": "ok"}