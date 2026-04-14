from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionState(str, Enum):
    IDLE = "idle"
    CAPTURING = "capturing"
    WAITING_FOR_MODEL = "waiting_for_model"
    RECOMMENDATION_READY = "recommendation_ready"
    AWAITING_NEXT = "awaiting_next"
    BLOCKED = "blocked"
    ERROR = "error"


class Speaker(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ActionType(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    TYPE_TEXT = "type_text"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    DRAG = "drag"
    WAIT_OBSERVE = "wait_observe"
    LOCATE_ONLY = "locate_only"
    DONE = "done"
    BLOCKED = "blocked"
    ASK_USER = "ask_user"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CoordinateSpace(str, Enum):
    DESKTOP_ABS_PX = "desktop_abs_px"
    CAPTURE_ABS_PX = "capture_abs_px"
    REQUEST_IMAGE_PX = "request_image_px"
    NORMALIZED = "normalized"


@dataclass
class ChatMessage:
    message_id: str
    speaker: Speaker
    text: str
    created_at: str = field(default_factory=utc_now_iso)
    step_index: Optional[int] = None

    @classmethod
    def create(cls, speaker: Speaker, text: str, step_index: Optional[int] = None) -> "ChatMessage":
        return cls(message_id=str(uuid4()), speaker=speaker, text=text, step_index=step_index)


@dataclass
class Point2D:
    x: float
    y: float
    coord_space: CoordinateSpace


@dataclass
class Region2D:
    left: float
    top: float
    width: float
    height: float
    coord_space: CoordinateSpace


@dataclass
class DisplayMonitor:
    left: int
    top: int
    width: int
    height: int


@dataclass
class CaptureMetadata:
    capture_id: str
    created_at: str
    image_path: str
    debug_image_path: Optional[str]
    virtual_left: int
    virtual_top: int
    capture_width: int
    capture_height: int
    request_width: int
    request_height: int
    monitors: list[DisplayMonitor]


@dataclass
class GuidedAction:
    # This is the app's normalized action contract. The rest of the program
    # works with this object instead of raw model output.
    action_id: str
    step_index: int
    source_response_id: str
    action_type: ActionType
    explanation: str
    expected_next_state: str
    user_instruction: str
    confidence: ConfidenceLevel
    advisory_only: bool
    executable: bool
    validation_notes: list[str] = field(default_factory=list)
    target_point: Optional[Point2D] = None
    target_region: Optional[Region2D] = None
    input_text: Optional[str] = None
    raw_model_payload: dict[str, Any] = field(default_factory=dict)
    mapped_screen_point: Optional[Point2D] = None
    is_terminal: bool = False


@dataclass
class SessionEvent:
    event_id: str
    event_type: str
    detail: dict[str, Any]
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(cls, event_type: str, detail: dict[str, Any]) -> "SessionEvent":
        return cls(event_id=str(uuid4()), event_type=event_type, detail=detail)


@dataclass
class SessionData:
    # SessionData is the single persisted source of truth for one operator run.
    session_id: str
    created_at: str
    updated_at: str
    state: SessionState
    model: str
    previous_response_id: Optional[str] = None
    step_index: int = 0
    summary: str = ""
    history: list[ChatMessage] = field(default_factory=list)
    captures: list[CaptureMetadata] = field(default_factory=list)
    actions: list[GuidedAction] = field(default_factory=list)
    last_error: Optional[str] = None

    @classmethod
    def create(cls, model: str) -> "SessionData":
        now = utc_now_iso()
        return cls(
            session_id=str(uuid4()),
            created_at=now,
            updated_at=now,
            state=SessionState.IDLE,
            model=model,
        )

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def session_dir_name(session: SessionData) -> str:
    return session.session_id


def path_to_string(path: Optional[Path]) -> Optional[str]:
    return str(path) if path is not None else None
