import logging
import json
import re
from typing import List, Dict, Any
from litellm import acompletion
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.default_prompt = (
            "Ты — виртуальный представитель кафедры ПМИТ. Ты эксперт-помощник. "
            "Если тебя просят написать код или создать проект, ВСЕГДА используй инструменты создания файлов. "
            "После вызова инструментов обязательно напиши краткий комментарий пользователю о том, что было сделано."
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
                            "relative_path": {"type": "string", "description": "Относительный путь к файлу"},
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
                            "relative_path": {"type": "string", "description": "Относительный путь к папке"}
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

    async def execute_tool(self, func_name: str, args: Dict) -> str:
        session_id = args.get("session_id")
        rel_path = args.get("relative_path")
        if not session_id or not rel_path:
            return "Ошибка: отсутствуют аргументы session_id или relative_path."

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

    def _manual_parse_json(self, text: str) -> List[Dict]:
        found_tools = []
        try:
            potential_jsons = re.findall(r'\{.*\}', text, re.DOTALL)
            for pj in potential_jsons:
                data = json.loads(pj)
                if "function" in data or ("name" in data and "arguments" in data):
                    found_tools.append(data)
        except:
            pass
        return found_tools

    async def get_response(self, user_input: str, history: List[Dict], session_id: str, use_tools: bool = True) -> Dict[
        str, Any]:
        messages = [{"role": "system", "content": self._get_system_prompt()}] + history
        prepended_input = f"[SESSION_ID: {session_id}] {user_input}"
        messages.append({"role": "user", "content": prepended_input})

        try:
            kwargs = {
                "model": settings.MODEL,
                "messages": messages,
                "api_base": settings.API_BASE,
                "api_key": settings.OLLAMA_API_KEY,
                "temperature": settings.TEMPERATURE,
                "timeout": 1800,
            }
            if use_tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"

            response = await acompletion(**kwargs)
            message = response.choices[0].message
            content = message.content or ""

            tool_calls_to_exec = []
            if use_tools and message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls_to_exec.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": json.loads(tc.function.arguments)
                    })
            elif use_tools:
                manual_tools = self._manual_parse_json(content)
                for mt in manual_tools:
                    name = mt.get("function") or mt.get("name")
                    args = mt.get("arguments") if isinstance(mt.get("arguments"), dict) else mt
                    tool_calls_to_exec.append({"id": "manual", "name": name, "args": args})

            if tool_calls_to_exec:
                messages.append(message)
                for tc in tool_calls_to_exec:
                    result = await self.execute_tool(tc["name"], tc["args"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", "manual"),
                        "name": tc["name"],
                        "content": result
                    })

                messages.append({"role": "user",
                                 "content": "Файлы созданы. Теперь кратко ответь пользователю на естественном языке, что именно ты сделал."})

                final_response = await acompletion(
                    model=settings.MODEL,
                    messages=messages,
                    api_base=settings.API_BASE,
                    api_key=settings.OLLAMA_API_KEY,
                    temperature=settings.TEMPERATURE
                )
                return {"text": final_response.choices[0].message.content, "has_files": True}

            return {"text": content, "has_files": False}
        except Exception as e:
            logger.error(f"AI Service Error: {e}")
            return {"text": f"Ошибка сервера: {str(e)}", "has_files": False}


ai_service = AIService()