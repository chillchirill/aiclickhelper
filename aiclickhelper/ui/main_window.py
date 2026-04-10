from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..controller import SessionController
from ..models import GuidedAction, Speaker
from ..overlay import OverlayWindow


class MainWindow(QMainWindow):
    def __init__(self, controller: SessionController, overlay: OverlayWindow) -> None:
        super().__init__()
        self._controller = controller
        self._overlay = overlay
        self._restore_after_capture = False

        self.setWindowTitle("AiClickHelper")
        self.resize(430, 760)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.Tool)

        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)
        root_layout.addWidget(self._build_panel())

        self._connect_signals()
        self._refresh_chat()
        self._refresh_action(None)

    def _build_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.status_label = QLabel("Status: idle")
        self.new_session_button = QPushButton("New Session")
        top_row.addWidget(self.status_label)
        top_row.addStretch(1)
        top_row.addWidget(self.new_session_button)
        layout.addLayout(top_row)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setAcceptRichText(True)
        layout.addWidget(self.chat_history, 1)

        action_card = QFrame()
        action_card.setFrameShape(QFrame.StyledPanel)
        action_layout = QVBoxLayout(action_card)
        action_layout.setSpacing(6)

        self.action_type_label = QLabel("No recommendation yet.")
        self.action_type_label.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.explanation_label = QLabel("Explanation will appear here.")
        self.explanation_label.setWordWrap(True)
        self.next_state_label = QLabel("Expected next state will appear here.")
        self.next_state_label.setWordWrap(True)
        self.instruction_label = QLabel("User instruction will appear here.")
        self.instruction_label.setWordWrap(True)
        self.confidence_label = QLabel("Confidence: -")
        self.validation_label = QLabel("Validation notes: none")
        self.validation_label.setWordWrap(True)

        action_layout.addWidget(self.action_type_label)
        action_layout.addWidget(self.explanation_label)
        action_layout.addWidget(self.next_state_label)
        action_layout.addWidget(self.instruction_label)
        action_layout.addWidget(self.confidence_label)
        action_layout.addWidget(self.validation_label)
        layout.addWidget(action_card, 0)

        layout.addWidget(QLabel("Prompt"))
        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText(
            "Describe what you want to do in the target application."
        )
        self.prompt_input.setMaximumBlockCount(200)
        self.prompt_input.setFixedHeight(100)
        self.send_button = QPushButton("Send")
        self.next_button = QPushButton("Next")
        self.next_button.setEnabled(False)
        button_row = QHBoxLayout()
        button_row.addWidget(self.next_button)
        button_row.addWidget(self.send_button)
        layout.addWidget(self.prompt_input)
        layout.addLayout(button_row)
        return panel

    def _connect_signals(self) -> None:
        self.send_button.clicked.connect(self._send_prompt)
        self.new_session_button.clicked.connect(self._controller.start_new_session)
        self.next_button.clicked.connect(self._controller.continue_after_next)
        self._controller.chatUpdated.connect(self._refresh_chat)
        self._controller.statusChanged.connect(self._set_status)
        self._controller.actionChanged.connect(self._refresh_action)
        self._controller.errorRaised.connect(self._show_error)
        self._controller.sessionReset.connect(self._handle_session_reset)
        self._controller.capturePreparationStarted.connect(self._prepare_for_capture)
        self._controller.capturePreparationFinished.connect(self._restore_after_capture_if_needed)

    def _send_prompt(self) -> None:
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        self.prompt_input.clear()
        self._controller.submit_user_prompt(prompt)

    def _refresh_chat(self) -> None:
        session = self._controller.session
        lines = []
        for message in session.history:
            prefix = {
                Speaker.USER: "User",
                Speaker.ASSISTANT: "Assistant",
                Speaker.SYSTEM: "System",
            }.get(message.speaker, message.speaker.value.title())
            body = message.text.replace("\n", "<br>")
            lines.append(
                f"<p><b>{prefix}</b> <span style='color:#7a869a;'>[{message.created_at}]</span><br>{body}</p>"
            )
        self.chat_history.setHtml("".join(lines) or "<p>No conversation yet.</p>")
        self.chat_history.moveCursor(QTextCursor.End)

    def _refresh_action(self, action: Optional[GuidedAction]) -> None:
        if action is None:
            self.action_type_label.setText("No recommendation yet.")
            self.explanation_label.setText("Explanation will appear here.")
            self.next_state_label.setText("Expected next state will appear here.")
            self.instruction_label.setText("User instruction will appear here.")
            self.confidence_label.setText("Confidence: -")
            self.validation_label.setText("Validation notes: none")
            self.next_button.setEnabled(False)
            self._overlay.clear_action()
            return

        self.action_type_label.setText(f"Action: {action.action_type.value}")
        self.explanation_label.setText(f"Why: {action.explanation}")
        self.next_state_label.setText(
            f"Expected next state: {action.expected_next_state}"
        )
        self.instruction_label.setText(f"Instruction: {action.user_instruction}")
        self.confidence_label.setText(f"Confidence: {action.confidence.value}")
        notes = "; ".join(action.validation_notes) if action.validation_notes else "none"
        self.validation_label.setText(f"Validation notes: {notes}")
        self.next_button.setEnabled(not action.is_terminal)

        if action.mapped_screen_point is not None and not action.is_terminal:
            self._overlay.show_action(action)
        else:
            self._overlay.clear_action()

    def _set_status(self, status: str) -> None:
        self.status_label.setText(f"Status: {status}")

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "AiClickHelper Error", message)

    def _handle_session_reset(self) -> None:
        self.prompt_input.clear()
        self.chat_history.clear()
        self._refresh_action(None)

    def _prepare_for_capture(self) -> None:
        self._restore_after_capture = self.isVisible()
        self._overlay.clear_action()
        if self._restore_after_capture:
            self.hide()

    def _restore_after_capture_if_needed(self) -> None:
        if not self._restore_after_capture:
            return
        self.show()
        self.raise_()
        self.activateWindow()
        self._restore_after_capture = False
