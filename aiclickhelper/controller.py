from __future__ import annotations

import traceback
from dataclasses import replace
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from .capture_service import CaptureService
from .config import AppConfig
from .coordinate_mapper import CoordinateMapper
from .models import (
    ActionType,
    CaptureMetadata,
    ChatMessage,
    GuidedAction,
    SessionData,
    SessionState,
    Speaker,
)
from .openai_adapter import OpenAIAdapter
from .response_normalizer import ResponseNormalizer
from .session_store import SessionStore


class TurnWorker(QObject):
    finished = pyqtSignal(object, str, str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        adapter: OpenAIAdapter,
        session: SessionData,
        prompt: str,
        screenshot_data_url: str,
    ) -> None:
        super().__init__()
        self._adapter = adapter
        self._session = session
        self._prompt = prompt
        self._screenshot_data_url = screenshot_data_url

    def run(self) -> None:
        try:
            response_id, assistant_text = self._adapter.request_guided_action(
                session=self._session,
                new_prompt=self._prompt,
                screenshot_data_url=self._screenshot_data_url,
            )
            self.finished.emit(self._session, response_id, assistant_text)
        except Exception as exc:
            detail = f"{exc}\n{traceback.format_exc()}"
            self.failed.emit(detail)


class SessionController(QObject):
    chatUpdated = pyqtSignal()
    statusChanged = pyqtSignal(str)
    actionChanged = pyqtSignal(object)
    screenshotChanged = pyqtSignal(str, str)
    errorRaised = pyqtSignal(str)
    sessionReset = pyqtSignal()
    capturePreparationStarted = pyqtSignal()
    capturePreparationFinished = pyqtSignal()

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._store = SessionStore(config)
        self._capture_service = CaptureService()
        self._mapper = CoordinateMapper()
        self._normalizer = ResponseNormalizer()
        self._adapter = OpenAIAdapter(config)

        self.session = self._store.create_session()
        self.current_action: Optional[GuidedAction] = None
        self.current_capture: Optional[CaptureMetadata] = None
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[TurnWorker] = None

        self._emit_status()

    @property
    def latest_capture_path(self) -> Optional[str]:
        if self.current_capture is None:
            return None
        return self.current_capture.image_path

    def start_new_session(self) -> None:
        self.session = self._store.create_session()
        self.current_action = None
        self.current_capture = None
        self._emit_status()
        self._store.append_event(
            self.session, "session_created", {"session_id": self.session.session_id}
        )
        self.sessionReset.emit()
        self.chatUpdated.emit()
        self.actionChanged.emit(None)

    def submit_user_prompt(self, prompt: str) -> None:
        prompt = prompt.strip()
        if not prompt:
            return
        if self._worker_thread is not None:
            self.errorRaised.emit("A model request is already in progress.")
            return

        self.session.history.append(
            ChatMessage.create(Speaker.USER, prompt, step_index=self.session.step_index)
        )
        self._store.append_event(self.session, "user_prompt_submitted", {"prompt": prompt})
        self._store.save_session(self.session)
        self.chatUpdated.emit()
        self._execute_turn(prompt)

    def continue_after_next(self) -> None:
        if self.current_action is None:
            self.errorRaised.emit("There is no active recommendation to continue from.")
            return
        if self._worker_thread is not None:
            self.errorRaised.emit("A model request is already in progress.")
            return

        continuation = (
            "The operator completed or reviewed the last recommended step. "
            "Continue from the new screen state."
        )
        if self.current_action.input_text:
            continuation += " The prior recommendation included text input."

        self.session.history.append(
            ChatMessage.create(
                Speaker.SYSTEM,
                continuation,
                step_index=self.session.step_index,
            )
        )
        self._store.append_event(
            self.session,
            "operator_continued",
            {
                "step_index": self.current_action.step_index,
                "action_type": self.current_action.action_type.value,
            },
        )
        self._store.save_session(self.session)
        self.chatUpdated.emit()
        QTimer.singleShot(
            self._config.pre_next_capture_delay_ms,
            lambda: self._execute_turn(continuation),
        )

    def _execute_turn(self, prompt: str) -> None:
        self.session.state = SessionState.CAPTURING
        self._emit_status()

        try:
            self.capturePreparationStarted.emit()
            QApplication.processEvents()
            QThread.msleep(self._config.capture_hide_delay_ms)
            # We always capture first so the model reasons over the exact state
            # the operator is currently seeing.
            capture = self._capture_current_screen()
        except Exception as exc:
            self._set_error(f"Screenshot capture failed: {exc}")
            return
        finally:
            self.capturePreparationFinished.emit()

        self.current_capture = capture
        self._store.save_session(self.session)
        self.screenshotChanged.emit(
            capture.image_path,
            capture.debug_image_path or "",
        )

        screenshot_data_url = self._capture_service.encode_image_data_url(
            Path(capture.image_path)
        )
        self.session.state = SessionState.WAITING_FOR_MODEL
        self._emit_status()

        worker_session = replace(self.session)
        worker_session.history = list(self.session.history)
        worker_session.actions = list(self.session.actions)
        worker_session.captures = list(self.session.captures)

        self._worker_thread = QThread(self)
        self._worker = TurnWorker(
            self._adapter,
            worker_session,
            prompt,
            screenshot_data_url,
        )
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_turn_success)
        self._worker.failed.connect(self._handle_turn_failure)
        self._worker.finished.connect(self._cleanup_worker)
        self._worker.failed.connect(self._cleanup_worker)
        self._worker_thread.start()

    def _capture_current_screen(self) -> CaptureMetadata:
        screenshots_dir = self._store.screenshots_dir(self.session)
        debug_dir = self._store.debug_dir(self.session)
        step_label = self.session.step_index + 1
        image_path = screenshots_dir / f"step-{step_label:03d}.png"
        debug_path = debug_dir / f"annotated-step-{step_label:03d}.png"
        capture = self._capture_service.capture_full_desktop(
            image_path=image_path,
            debug_image_path=debug_path if self._config.save_debug_images else None,
            guided_action=self.current_action,
        )
        self.session.captures.append(capture)
        self._store.append_event(
            self.session,
            "screenshot_captured",
            {
                "image_path": capture.image_path,
                "virtual_left": capture.virtual_left,
                "virtual_top": capture.virtual_top,
                "capture_width": capture.capture_width,
                "capture_height": capture.capture_height,
            },
        )
        return capture

    def _handle_turn_success(
        self,
        _worker_session: SessionData,
        response_id: str,
        assistant_text: str,
    ) -> None:
        if response_id:
            self.session.previous_response_id = response_id
        self.session.step_index += 1

        action = self._normalizer.normalize(
            response_id=response_id or "unknown-response",
            step_index=self.session.step_index,
            assistant_text=assistant_text,
        )

        if self.current_capture is not None:
            # Model coordinates live in screenshot space; map them once here
            # before the UI and overlay consume the action.
            action = self._mapper.map_action(action, self.current_capture)
            if self._config.save_debug_images and self.current_capture.debug_image_path:
                self._capture_service.annotate_capture(
                    image_path=Path(self.current_capture.image_path),
                    debug_image_path=Path(self.current_capture.debug_image_path),
                    guided_action=action,
                    capture=self.current_capture,
                )
                self.screenshotChanged.emit(
                    self.current_capture.image_path,
                    self.current_capture.debug_image_path,
                )

        self.current_action = action
        self.session.actions.append(action)
        self.session.history.append(
            ChatMessage.create(
                Speaker.ASSISTANT,
                self._assistant_text_for_history(action),
                step_index=self.session.step_index,
            )
        )
        self.session.summary = self._build_summary()

        if action.action_type == ActionType.BLOCKED:
            self.session.state = SessionState.BLOCKED
        elif action.is_terminal:
            self.session.state = SessionState.RECOMMENDATION_READY
        else:
            self.session.state = SessionState.AWAITING_NEXT

        self._store.append_event(
            self.session,
            "guided_action_ready",
            {
                "response_id": response_id,
                "action_type": action.action_type.value,
                "confidence": action.confidence.value,
                "validation_notes": action.validation_notes,
            },
        )
        self._store.save_session(self.session)
        self._emit_status()
        self.chatUpdated.emit()
        self.actionChanged.emit(action)

    def _handle_turn_failure(self, detail: str) -> None:
        self._set_error(f"OpenAI request failed.\n{detail}")

    def _cleanup_worker(self, *_args) -> None:
        if self._worker_thread is not None:
            self._worker_thread.quit()
            self._worker_thread.wait()
        self._worker_thread = None
        self._worker = None

    def _set_error(self, message: str) -> None:
        self.session.state = SessionState.ERROR
        self.session.last_error = message
        self._store.append_event(self.session, "error", {"message": message})
        self._store.save_session(self.session)
        self._emit_status()
        self.errorRaised.emit(message)

    def _emit_status(self) -> None:
        self.statusChanged.emit(self.session.state.value)

    def _assistant_text_for_history(self, action: GuidedAction) -> str:
        parts = [
            f"Recommended action: {action.action_type.value}",
            f"Why: {action.explanation}",
            f"Next: {action.expected_next_state}",
            f"Instruction: {action.user_instruction}",
        ]
        if action.validation_notes:
            parts.append("Notes: " + "; ".join(action.validation_notes))
        return "\n".join(parts)

    def _build_summary(self) -> str:
        recent = self.session.actions[-5:]
        if not recent:
            return ""
        return " | ".join(
            f"step {action.step_index}: {action.action_type.value} -> {action.expected_next_state}"
            for action in recent
        )
