from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class MemoryStore:
    """Simple JSON-backed memory for per-user roleplay sessions."""

    def __init__(self, filepath: str = "memory.json") -> None:
        self.path = Path(filepath)
        self._lock = Lock()
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, payload: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def ensure_user(self, user_id: int) -> dict[str, Any]:
        key = str(user_id)
        with self._lock:
            payload = self._read()
            if key not in payload:
                payload[key] = {
                    "selected_story": None,
                    "history": [],
                }
                self._write(payload)
            return payload[key]

    def set_story(self, user_id: int, story: dict[str, Any]) -> None:
        key = str(user_id)
        with self._lock:
            payload = self._read()
            payload.setdefault(key, {"selected_story": None, "history": []})
            payload[key]["selected_story"] = story
            payload[key]["history"] = []
            self._write(payload)

    def get_story(self, user_id: int) -> dict[str, Any] | None:
        key = str(user_id)
        with self._lock:
            payload = self._read()
            return payload.get(key, {}).get("selected_story")

    def append_turn(self, user_id: int, role: str, text: str) -> None:
        key = str(user_id)
        with self._lock:
            payload = self._read()
            payload.setdefault(key, {"selected_story": None, "history": []})
            payload[key].setdefault("history", [])
            payload[key]["history"].append({"role": role, "text": text})
            payload[key]["history"] = payload[key]["history"][-20:]
            self._write(payload)

    def get_history(self, user_id: int) -> list[dict[str, str]]:
        key = str(user_id)
        with self._lock:
            payload = self._read()
            return payload.get(key, {}).get("history", [])
