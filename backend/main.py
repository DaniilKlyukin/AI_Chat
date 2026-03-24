import os
import asyncio
from pathlib import Path
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.agent import AIAgent

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = AIAgent()
sessions: Dict[str, List[Dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]
    history_for_agent = list(history)
    history.append({"role": "user", "content": req.message})

    async def process_message():
        try:
            ai_text = await agent.get_response(user_input=req.message, history=history_for_agent)
            history.append({"role": "assistant", "content": ai_text})
            return ai_text
        except Exception:
            err_msg = "Произошла ошибка при обработке запроса."
            history.append({"role": "assistant", "content": err_msg})
            return err_msg

    task = asyncio.create_task(process_message())

    try:
        ai_text = await asyncio.shield(task)
        return {"status": "success", "response": ai_text}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history")
async def get_history(session_id: str):
    history = sessions.get(session_id, [])
    return {"status": "success", "history": history}


@app.post("/api/system/clear-history")
async def clear_history(session_id: str):
    if session_id in sessions:
        sessions[session_id] = []
    return {"status": "ok"}


@app.get("/")
async def serve_index(request: Request):
    js_path = FRONTEND_DIR / "script.js"
    css_path = FRONTEND_DIR / "style.css"
    js_ver = os.path.getmtime(js_path) if js_path.exists() else 1
    css_ver = os.path.getmtime(css_path) if css_path.exists() else 1

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"js_ver": js_ver, "css_ver": css_ver}
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)