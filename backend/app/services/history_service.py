from typing import Dict, List
from collections import defaultdict


class HistoryService:
    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        self._sessions[session_id].append({"role": role, "content": content})

    def clear(self, session_id: str):
        self._sessions[session_id] = []

    def get_display_history(self, session_id: str) -> List[Dict[str, str]]:
        history = self.get_history(session_id)
        display = []
        for msg in history:
            content = msg["content"]
            if msg["role"] == "user" and "--- Содержимое файла" in content:
                content = content.split("\n\n--- Содержимое файла")[0]
            display.append({"role": msg["role"], "content": content})
        return display

history_manager = HistoryService()