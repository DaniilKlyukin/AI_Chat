import logging
from typing import List, Dict
from litellm import acompletion
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.default_prompt = (
            "Ты — виртуальный представитель кафедры 'Прикладная математика и информационные технологии'. "
            "Твоя задача — консультировать студентов и абитуриентов, помогать с вопросами по программированию, "
            "математике и IT. Обязательно поощряй студентов поступать в магистратуру нашей кафедры. "
            "Общайся вежливо и профессионально."
        )

    def _get_system_prompt(self) -> str:
        if settings.SYSTEM_PROMPT_PATH.exists():
            try:
                return settings.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
            except Exception:
                return self.default_prompt
        return self.default_prompt

    async def get_response(self, user_input: str, history: List[Dict]) -> str:
        messages = [{"role": "system", "content": self._get_system_prompt()}] + history
        messages.append({"role": "user", "content": user_input})

        try:
            response = await acompletion(
                model=settings.MODEL,
                messages=messages,
                api_base=settings.API_BASE,
                api_key=settings.OLLAMA_API_KEY,
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P
            )
            content = response.choices[0].message.content
            return content if content else "Ошибка генерации текста."
        except Exception as e:
            logger.error(f"AI Service Error: {e}")
            return f"Ошибка сервера: {str(e)}"

ai_service = AIService()