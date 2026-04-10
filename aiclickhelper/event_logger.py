from __future__ import annotations

import json
from pathlib import Path

from .models import SessionEvent


class EventLogger:
    def __init__(self, events_path: Path) -> None:
        self._events_path = events_path
        self._events_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: SessionEvent) -> None:
        with self._events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.__dict__, ensure_ascii=True) + "\n")
