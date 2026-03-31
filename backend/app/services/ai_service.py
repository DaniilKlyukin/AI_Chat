import logging
import time
import os
from typing import List, Dict, Any
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.history_service import history_manager
from app.services.file_service import FileService

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.API_KEY)

    def _count_tokens(self, model: str, contents: List[types.Content]) -> int:
        try:
            return self.client.models.count_tokens(model=model, contents=contents).total_tokens
        except:
            return 0

    async def _summarize_history(self, session_id: str, model_id: str, history: List[Dict]):
        if len(history) < 4: return

        to_summarize = history[:-2]
        text_to_shrink = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])

        prompt = f"Сделай очень краткое техническое резюме этого диалога (суть, принятые решения, важный код). Максимально сожми текст:\n\n{text_to_shrink}"

        try:
            # Для саммаризации используем упрощенный вызов без system_instruction
            res = self.client.models.generate_content(
                model=model_id,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])]
            )
            summary_text = f"[Контекст предыдущего диалога: {res.text}]"
            history_manager.replace_with_summary(session_id, len(to_summarize), summary_text)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")

    async def get_response(self, user_input: str, history: List[Dict], session_id: str, requested_model: str,
                           file_paths: List[str]) -> Dict:
        system_instr = settings.SYSTEM_PROMPT_PATH.read_text(
            encoding="utf-8") if settings.SYSTEM_PROMPT_PATH.exists() else "Assistant"

        file_text_bundle = ""
        for fp in file_paths:
            content = FileService.get_file_content_safe(fp)
            file_text_bundle += f"\n\n--- FILE: {os.path.basename(fp)} ---\n{content}\n--- END ---"

        current_user_text = user_input + file_text_bundle

        input_parts = [types.Part(text=current_user_text)]
        input_tokens = self._count_tokens(requested_model, [types.Content(role="user", parts=input_parts)])

        effective_model = requested_model
        if input_tokens > 12000:
            effective_model = settings.MODEL_STRONG

        cooldown = settings.COOLDOWN_FAST if effective_model == settings.MODEL_FAST else settings.COOLDOWN_STRONG
        wait = history_manager.check_rate_limit(session_id, effective_model, cooldown)
        if wait > 0:
            return {"text": f"ЛИМИТ:{wait}", "model": effective_model}

        contents = []
        is_gemma = "gemma" in effective_model.lower()

        if is_gemma:
            contents.append(types.Content(role="user", parts=[types.Part(text=f"SYSTEM INSTRUCTION: {system_instr}")]))
            contents.append(
                types.Content(role="model", parts=[types.Part(text="Understood. I will follow these instructions.")]))

        # Добавляем историю
        for m in history:
            contents.append(types.Content(role="user" if m["role"] == "user" else "model",
                                          parts=[types.Part(text=m["content"])]))

        current_parts = [types.Part(text=current_user_text)]
        if not is_gemma and effective_model == settings.MODEL_STRONG:
            current_parts = [types.Part(text=user_input)]
            for fp in file_paths:
                try:
                    uploaded = self.client.files.upload(path=fp)
                    while uploaded.state.name == "PROCESSING":
                        time.sleep(1)
                        uploaded = self.client.files.get(name=uploaded.name)
                    current_parts.append(types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type))
                except:
                    pass

        contents.append(types.Content(role="user", parts=current_parts))

        if is_gemma and self._count_tokens(effective_model, contents) > 13000:
            await self._summarize_history(session_id, effective_model, history)
            new_history = history_manager.get_history(session_id)
            return await self.get_response(user_input, new_history, session_id, requested_model, file_paths)

        try:
            config = types.GenerateContentConfig(temperature=0.7)
            if not is_gemma:
                config.system_instruction = system_instr

            res = self.client.models.generate_content(model=effective_model, contents=contents, config=config)
            history_manager.update_timestamp(session_id, effective_model)
            return {"text": res.text, "model": effective_model}
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"text": f"Ошибка API: {str(e)}", "model": effective_model}


ai_service = AIService()