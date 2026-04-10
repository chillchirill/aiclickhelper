from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_data_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "AiClickHelper"
    return Path.cwd() / ".aiclickhelper-data"


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "AiClickHelper"
    model: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL", "gpt-5.4"))
    max_response_turns: int = 24
    cursor_hide_radius_px: int = 28
    openai_timeout_seconds: int = 60
    pre_next_capture_delay_ms: int = 250
    capture_hide_delay_ms: int = 150
    save_debug_images: bool = True
    data_root: Path = _default_data_root()

    @property
    def sessions_root(self) -> Path:
        return self.data_root / "sessions"
