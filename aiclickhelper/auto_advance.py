from __future__ import annotations

import ctypes
import time
from typing import Optional

import mss
from PIL import Image, ImageChops, ImageStat
from PyQt5.QtCore import QObject, QTimer

from .config import AppConfig
from .controller import SessionController
from .models import ActionType, GuidedAction, SessionState


VK_LBUTTON = 0x01
VK_RETURN = 0x0D


class AutoAdvanceController(QObject):
    def __init__(self, config: AppConfig, controller: SessionController) -> None:
        super().__init__()
        self._config = config
        self._controller = controller
        self._current_action: Optional[GuidedAction] = None
        self._armed = False
        self._confirmed = False
        self._baseline_image: Optional[Image.Image] = None
        self._confirm_started_at = 0.0
        self._prev_left_down = False
        self._prev_enter_down = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(config.auto_advance_poll_ms)

    def set_action(self, action: Optional[GuidedAction]) -> None:
        self._current_action = action
        self._armed = False
        self._confirmed = False
        self._baseline_image = None
        self._confirm_started_at = 0.0

    def handle_proximity_changed(self, is_near: bool) -> None:
        if self._current_action is None or self._current_action.is_terminal:
            return

        if is_near and not self._armed:
            self._armed = True
            self._baseline_image = self._capture_signature_image()
            return

        if not is_near and not self._confirmed:
            self._armed = False
            self._baseline_image = None

    def _poll(self) -> None:
        if self._current_action is None or self._current_action.is_terminal:
            return
        if self._controller.session.state != SessionState.AWAITING_NEXT:
            return
        if not self._armed:
            self._remember_key_states()
            return

        if not self._confirmed:
            if self._is_confirmation_detected():
                self._confirmed = True
                self._confirm_started_at = time.monotonic()
            self._remember_key_states()
            return

        if self._screen_changed():
            self._trigger_continue()
            return

        if (time.monotonic() - self._confirm_started_at) * 1000 >= self._config.auto_advance_timeout_ms:
            self._trigger_continue()

    def _trigger_continue(self) -> None:
        self._armed = False
        self._confirmed = False
        self._baseline_image = None
        self._confirm_started_at = 0.0
        self._controller.continue_after_next()

    def _is_confirmation_detected(self) -> bool:
        if self._expects_enter():
            return self._rising_edge(VK_RETURN, self._prev_enter_down)
        return self._rising_edge(VK_LBUTTON, self._prev_left_down)

    def _expects_enter(self) -> bool:
        return self._current_action is not None and self._current_action.action_type == ActionType.TYPE_TEXT

    def _rising_edge(self, vk_code: int, previous: bool) -> bool:
        current = bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
        return current and not previous

    def _remember_key_states(self) -> None:
        self._prev_left_down = bool(ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        self._prev_enter_down = bool(ctypes.windll.user32.GetAsyncKeyState(VK_RETURN) & 0x8000)

    def _capture_signature_image(self) -> Optional[Image.Image]:
        try:
            with mss.mss() as sct:
                shot = sct.grab(sct.monitors[0])
                image = Image.frombytes("RGB", shot.size, shot.rgb)
            return image.convert("L").resize((96, 54))
        except Exception:
            return None

    def _screen_changed(self) -> bool:
        if self._baseline_image is None:
            return False

        current = self._capture_signature_image()
        if current is None:
            return False

        diff = ImageChops.difference(self._baseline_image, current)
        mean = ImageStat.Stat(diff).mean[0]
        return mean >= 3.0
