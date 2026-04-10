from __future__ import annotations

from math import hypot

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .models import Point2D
from .overlay import current_cursor_position


class CursorProximityWatcher(QObject):
    proximityChanged = pyqtSignal(bool)

    def __init__(self, radius_px: int) -> None:
        super().__init__()
        self._radius_px = radius_px
        self._target: Point2D | None = None
        self._is_near = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_cursor)
        self._timer.start(40)

    def set_target(self, target: Point2D | None) -> None:
        self._target = target
        if target is None and self._is_near:
            self._is_near = False
            self.proximityChanged.emit(False)

    def _poll_cursor(self) -> None:
        if self._target is None:
            return

        cursor = current_cursor_position()
        if cursor is None:
            return

        distance = hypot(cursor[0] - self._target.x, cursor[1] - self._target.y)
        is_near = distance <= self._radius_px
        if is_near != self._is_near:
            self._is_near = is_near
            self.proximityChanged.emit(is_near)
