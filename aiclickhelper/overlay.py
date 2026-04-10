from __future__ import annotations

import ctypes
from typing import Optional

from PyQt5.QtCore import QPoint, QRect, QTimer, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

from .models import GuidedAction, Point2D


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class OverlayWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self._target_point: Optional[Point2D] = None
        self._target_label = ""
        self._visible_marker = False
        self._pulse_radius = 28

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._advance_pulse)
        self._pulse_timer.start(50)

        self._sync_geometry()
        self.hide()

    def show_action(self, action: GuidedAction) -> None:
        if action.mapped_screen_point is None or action.is_terminal:
            self.clear_action()
            return

        self._target_point = action.mapped_screen_point
        self._target_label = self._label_for_action(action)
        self._visible_marker = True
        self._sync_geometry()
        self._apply_click_through()
        self.show()
        self.raise_()
        self.update()

    def clear_action(self) -> None:
        self._target_point = None
        self._target_label = ""
        self._visible_marker = False
        self.hide()
        self.update()

    def hide_marker_only(self) -> None:
        self._visible_marker = False
        self.update()

    def show_marker_only(self) -> None:
        if self._target_point is None:
            return
        self._visible_marker = True
        self.show()
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        if not self._visible_marker or self._target_point is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        local_x = int(round(self._target_point.x - self.geometry().left()))
        local_y = int(round(self._target_point.y - self.geometry().top()))

        glow_color = QColor(255, 90, 90, 180)
        ring_color = QColor(255, 210, 80, 230)
        text_bg = QColor(20, 24, 32, 220)
        text_fg = QColor(250, 250, 250)

        painter.setPen(QPen(glow_color, 8))
        painter.drawEllipse(QPoint(local_x, local_y), self._pulse_radius + 6, self._pulse_radius + 6)

        painter.setPen(QPen(ring_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(local_x, local_y), self._pulse_radius, self._pulse_radius)
        painter.drawLine(local_x - 16, local_y, local_x + 16, local_y)
        painter.drawLine(local_x, local_y - 16, local_x, local_y + 16)

        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(local_x, local_y), 5, 5)

        if self._target_label:
            painter.setFont(QFont("Segoe UI", 10))
            metrics = painter.fontMetrics()
            padding = 8
            text_width = metrics.horizontalAdvance(self._target_label)
            rect = QRect(
                local_x + 18,
                local_y - 34,
                text_width + (padding * 2),
                metrics.height() + (padding * 2),
            )
            painter.setBrush(text_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 8, 8)
            painter.setPen(text_fg)
            painter.drawText(
                rect.adjusted(padding, padding, -padding, -padding),
                Qt.AlignLeft | Qt.AlignVCenter,
                self._target_label,
            )

    def _advance_pulse(self) -> None:
        self._pulse_radius += 1
        if self._pulse_radius > 34:
            self._pulse_radius = 26
        if self.isVisible():
            self.update()

    def _label_for_action(self, action: GuidedAction) -> str:
        if action.action_type.value == "type_text":
            return "Type here"
        if action.action_type.value == "click":
            return "Click here"
        if action.action_type.value == "double_click":
            return "Double-click here"
        if action.action_type.value == "locate_only":
            return "Target area"
        return action.action_type.value.replace("_", " ").title()

    def _sync_geometry(self) -> None:
        left = ctypes.windll.user32.GetSystemMetrics(76)
        top = ctypes.windll.user32.GetSystemMetrics(77)
        width = ctypes.windll.user32.GetSystemMetrics(78)
        height = ctypes.windll.user32.GetSystemMetrics(79)
        self.setGeometry(left, top, width, height)

    def _apply_click_through(self) -> None:
        hwnd = int(self.winId())
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, -20)
        style |= 0x00080000
        style |= 0x00000020
        style |= 0x08000000
        user32.SetWindowLongW(hwnd, -20, style)


def current_cursor_position() -> Optional[tuple[int, int]]:
    point = POINT()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        return None
    return point.x, point.y
