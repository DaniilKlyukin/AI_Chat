import uvicorn
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import router
from app.core.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")
app.mount("/", StaticFiles(directory=str(settings.FRONTEND_DIR)), name="static")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()

if __name__ == "__main__":
    ip = get_ip()
    port = 8000
    print(f"\nAI Chat запущен: http://{ip}:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)