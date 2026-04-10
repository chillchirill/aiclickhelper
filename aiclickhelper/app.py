from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from .config import AppConfig
from .controller import SessionController
from .cursor_watcher import CursorProximityWatcher
from .dpi import enable_windows_dpi_awareness
from .overlay import OverlayWindow
from .ui.main_window import MainWindow


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name and name not in os.environ:
            os.environ[name] = value


def main() -> int:
    load_dotenv()
    enable_windows_dpi_awareness()
    app = QApplication(sys.argv)
    app.setApplicationName("AiClickHelper")

    config = AppConfig()
    controller = SessionController(config)
    overlay = OverlayWindow()
    watcher = CursorProximityWatcher(radius_px=config.cursor_hide_radius_px)

    def handle_action_change(action) -> None:
        target = getattr(action, "mapped_screen_point", None) if action is not None else None
        watcher.set_target(target)

    controller.actionChanged.connect(handle_action_change)
    watcher.proximityChanged.connect(
        lambda is_near: overlay.hide_marker_only() if is_near else overlay.show_marker_only()
    )

    window = MainWindow(controller, overlay)
    window.show()
    return app.exec_()
