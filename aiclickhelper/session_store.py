from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .config import AppConfig
from .event_logger import EventLogger
from .models import SessionData, SessionEvent, session_dir_name


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _to_json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    return value


class SessionStore:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._config.sessions_root.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> SessionData:
        session = SessionData.create(model=self._config.model)
        self.save_session(session)
        return session

    def session_root(self, session: SessionData) -> Path:
        return self._config.sessions_root / session_dir_name(session)

    def screenshots_dir(self, session: SessionData) -> Path:
        path = self.session_root(session) / "screenshots"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def debug_dir(self, session: SessionData) -> Path:
        path = self.session_root(session) / "debug"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def session_file(self, session: SessionData) -> Path:
        return self.session_root(session) / "session.json"

    def event_logger(self, session: SessionData) -> EventLogger:
        return EventLogger(self.session_root(session) / "events.jsonl")

    def save_session(self, session: SessionData) -> None:
        root = self.session_root(session)
        root.mkdir(parents=True, exist_ok=True)
        session.touch()
        payload = _to_json_safe(session)
        with self.session_file(session).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)

    def append_event(self, session: SessionData, event_type: str, detail: dict) -> None:
        logger = self.event_logger(session)
        logger.append(SessionEvent.create(event_type=event_type, detail=detail))
