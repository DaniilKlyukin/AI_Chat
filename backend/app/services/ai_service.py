import logging
import json
from typing import List, Dict, Any
from litellm import acompletion
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.default_prompt = (
            "Ты — виртуальный представитель кафедры ПМИТ. Ты можешь создавать файлы и проекты. "
            "Если тебя просят написать код или создать проект, используй инструменты создания файлов. "
            "Всегда старайся структурировать проект по папкам."
        )
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Создает файл с указанным содержимым",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "relative_path": {"type": "string",
                                              "description": "Путь к файлу внутри проекта, например 'src/main.py'"},
                            "content": {"type": "string", "description": "Содержимое файла"}
                        },
                        "required": ["relative_path", "content", "session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_directory",
                    "description": "Создает папку",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "relative_path": {"type": "string", "description": "Путь к папке, например 'assets/images'"}
                        },
                        "required": ["relative_path", "session_id"]
                    }
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        if settings.SYSTEM_PROMPT_PATH.exists():
            try:
                return settings.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
            except Exception:
                return self.default_prompt
        return self.default_prompt

    async def execute_tool(self, tool_call) -> str:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        session_id = args.get("session_id")
        rel_path = args.get("relative_path")

        base_path = settings.STORAGE_DIR / session_id
        base_path.mkdir(exist_ok=True)

        target_path = (base_path / rel_path).resolve()

        if not str(target_path).startswith(str(base_path.resolve())):
            return "Ошибка: выход за пределы разрешенной директории."

        if func_name == "create_file":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(args.get("content", ""), encoding="utf-8")
            return f"Файл {rel_path} успешно создан."

        elif func_name == "create_directory":
            target_path.mkdir(parents=True, exist_ok=True)
            return f"Директория {rel_path} создана."

        return "Неизвестная функция."

    async def get_response(self, user_input: str, history: List[Dict], session_id: str) -> Dict[str, Any]:
        messages = [{"role": "system", "content": self._get_system_prompt()}] + history

        prepended_input = f"[SESSION_ID: {session_id}] {user_input}"
        messages.append({"role": "user", "content": prepended_input})

        try:
            response = await acompletion(
                model=settings.MODEL,
                messages=messages,
                tools=self.tools,
                api_base=settings.API_BASE,
                api_key=settings.OLLAMA_API_KEY,
                temperature=settings.TEMPERATURE
            )

            message = response.choices[0].message

            if message.tool_calls:
                messages.append(message)
                for tool_call in message.tool_calls:
                    result = await self.execute_tool(tool_call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result
                    })

                final_response = await acompletion(
                    model=settings.MODEL,
                    messages=messages,
                    api_base=settings.API_BASE,
                    api_key=settings.OLLAMA_API_KEY
                )
                return {"text": final_response.choices[0].message.content, "has_files": True}

            return {"text": message.content, "has_files": False}
        except Exception as e:
            logger.error(f"AI Service Error: {e}")
            return {"text": f"Ошибка сервера: {str(e)}", "has_files": False}


ai_service = AIService()