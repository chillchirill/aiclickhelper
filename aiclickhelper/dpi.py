from __future__ import annotations

import ctypes


def enable_windows_dpi_awareness() -> None:
    try:
        awareness_context = ctypes.c_void_p(-4)
        user32 = ctypes.windll.user32
        user32.SetProcessDpiAwarenessContext(awareness_context)
    except Exception:
        try:
            shcore = ctypes.windll.shcore
            shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
