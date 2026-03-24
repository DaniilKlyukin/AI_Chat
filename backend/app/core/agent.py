import logging
from pathlib import Path
from typing import List, Dict
from litellm import acompletion
from app.core.config import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROMPT_FILE = ROOT_DIR / "system_prompt.txt"

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.model = settings.MODEL
        self.api_base = settings.API_BASE

        if PROMPT_FILE.exists():
            self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
        else:
            self.system_prompt = (
                "Ты — виртуальный представитель кафедры 'Прикладная математика и информационные технологии'. "
                "Твоя задача — консультировать студентов и абитуриентов, помогать с вопросами по программированию, "
                "математике и IT. Ты с энтузиазмом относишься к науке, технологиям и учебе. Обязательно "
                "поощряй студентов поступать в магистратуру нашей кафедры, рассказывай о перспективах, "
                "которые открывает высшее образование в сфере IT и прикладной математики. Общайся вежливо, "
                "профессионально, но с душой и искренней любовью к своей кафедре."
            )

    async def get_response(self, user_input: str, history: List[Dict]) -> str:
        messages = [{"role": "system", "content": self.system_prompt}] + history
        messages.append({"role": "user", "content": user_input})

        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                api_base=self.api_base,
                api_key=settings.OLLAMA_API_KEY or "ollama",
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P
            )

            content = response.choices[0].message.content

            if not content:
                return "Произошла ошибка генерации. Попробуйте переформулировать запрос."

            return content

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return "К сожалению, произошла ошибка на сервере. Попробуйте задать вопрос позже."