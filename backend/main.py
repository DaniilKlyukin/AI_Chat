from pathlib import Path
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.agent import AIAgent
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

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
    temperature: float = 0.3
    top_p: float = 0.8

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        if req.session_id not in sessions:
            sessions[req.session_id] = []
            
        history = sessions[req.session_id]
        
        ai_text = await agent.get_response(
            user_input=req.message,
            history=history,
            temperature=req.temperature,
            top_p=req.top_p
        )
        
        history.append({"role": "user", "content": req.message})
        history.append({"role": "assistant", "content": ai_text})
        
        return {"status": "success", "response": ai_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/state")
async def get_state():
    return {"model": settings.MODEL}

@app.post("/api/system/clear-history")
async def clear_history(session_id: str):
    if session_id in sessions:
        sessions[session_id] = []
    return {"status": "ok"}

@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)