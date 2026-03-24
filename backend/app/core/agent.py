from pathlib import Path
from typing import List, Dict
from litellm import acompletion
from app.core.config import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROMPT_FILE = ROOT_DIR / "system_prompt.txt"

class AIAgent:
    def __init__(self):
        self.model = settings.MODEL
        self.api_base = settings.API_BASE
        
        if PROMPT_FILE.exists():
            self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
        else:
            self.system_prompt = "Ты — ИИ-ассистент."

    async def get_response(self, user_input: str, history: List[Dict], temperature: float, top_p: float) -> str:
        messages = [{"role": "system", "content": self.system_prompt}] + history
        messages.append({"role": "user", "content": user_input})

        response = await acompletion(
            model=self.model,
            messages=messages,
            api_base=self.api_base,
            api_key=settings.OLLAMA_API_KEY,
            temperature=temperature,
            top_p=top_p
        )

        return response.choices[0].message.content or ""