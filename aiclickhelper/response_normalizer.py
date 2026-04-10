from __future__ import annotations

import json
import re
from typing import Any, Optional
from uuid import uuid4

from .models import (
    ActionType,
    ConfidenceLevel,
    CoordinateSpace,
    GuidedAction,
    Point2D,
    Region2D,
)


class ResponseNormalizer:
    def normalize(
        self,
        response_id: str,
        step_index: int,
        assistant_text: str,
    ) -> GuidedAction:
        notes: list[str] = []
        payload = self._extract_json_payload(assistant_text)
        if payload is None:
            notes.append("Could not parse model response as JSON; using safe blocked fallback.")
            return self._fallback_action(response_id, step_index, assistant_text, notes)

        action_type = self._parse_action_type(payload.get("action_type"), notes)
        target_point = self._parse_point(payload.get("target_point"), notes)
        target_region = self._parse_region(payload.get("target_region"), notes)
        confidence = self._parse_confidence(payload.get("confidence"))

        explanation = self._string_or_default(
            payload.get("explanation"),
            "The model did not provide a usable explanation.",
        )
        expected_next_state = self._string_or_default(
            payload.get("expected_next_state"),
            "The model did not describe the expected next state.",
        )
        user_instruction = self._string_or_default(
            payload.get("user_instruction"),
            "Review the current screen and continue carefully.",
        )
        advisory_only = bool(payload.get("advisory_only", False))
        executable = bool(payload.get("executable", False))
        input_text = self._optional_string(payload.get("input_text"))

        if action_type in {ActionType.BLOCKED, ActionType.DONE, ActionType.ASK_USER}:
            advisory_only = True
            executable = False

        if confidence == ConfidenceLevel.LOW:
            advisory_only = True
            executable = False

        if action_type not in {ActionType.DONE, ActionType.BLOCKED, ActionType.ASK_USER}:
            if target_point is None and target_region is None:
                notes.append("Interactive action is missing target coordinates.")
                advisory_only = True
                executable = False

        return GuidedAction(
            action_id=str(uuid4()),
            step_index=step_index,
            source_response_id=response_id,
            action_type=action_type,
            explanation=explanation,
            expected_next_state=expected_next_state,
            user_instruction=user_instruction,
            confidence=confidence,
            advisory_only=advisory_only,
            executable=executable,
            validation_notes=notes,
            target_point=target_point,
            target_region=target_region,
            input_text=input_text,
            raw_model_payload=payload,
            is_terminal=action_type in {ActionType.DONE, ActionType.BLOCKED},
        )

    def _fallback_action(
        self,
        response_id: str,
        step_index: int,
        assistant_text: str,
        notes: list[str],
    ) -> GuidedAction:
        return GuidedAction(
            action_id=str(uuid4()),
            step_index=step_index,
            source_response_id=response_id,
            action_type=ActionType.BLOCKED,
            explanation="The model response could not be normalized into a guided action.",
            expected_next_state="The operator should inspect the raw assistant text and retry.",
            user_instruction=assistant_text.strip() or "Retry the request.",
            confidence=ConfidenceLevel.LOW,
            advisory_only=True,
            executable=False,
            validation_notes=notes,
            raw_model_payload={"raw_text": assistant_text},
            is_terminal=True,
        )

    def _extract_json_payload(self, assistant_text: str) -> Optional[dict[str, Any]]:
        text = assistant_text.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if fenced_match:
            try:
                parsed = json.loads(fenced_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None
        return None

    def _parse_action_type(self, raw_value: Any, notes: list[str]) -> ActionType:
        if isinstance(raw_value, str):
            try:
                return ActionType(raw_value)
            except ValueError:
                notes.append(f"Unknown action_type '{raw_value}', falling back to blocked.")
        else:
            notes.append("Missing action_type, falling back to blocked.")
        return ActionType.BLOCKED

    def _parse_point(self, raw_value: Any, notes: list[str]) -> Optional[Point2D]:
        if not isinstance(raw_value, dict):
            return None
        try:
            return Point2D(
                x=float(raw_value["x"]),
                y=float(raw_value["y"]),
                coord_space=CoordinateSpace(raw_value.get("coord_space", CoordinateSpace.REQUEST_IMAGE_PX.value)),
            )
        except (KeyError, TypeError, ValueError):
            notes.append("Invalid target_point payload.")
            return None

    def _parse_region(self, raw_value: Any, notes: list[str]) -> Optional[Region2D]:
        if not isinstance(raw_value, dict):
            return None
        try:
            return Region2D(
                left=float(raw_value["left"]),
                top=float(raw_value["top"]),
                width=float(raw_value["width"]),
                height=float(raw_value["height"]),
                coord_space=CoordinateSpace(raw_value.get("coord_space", CoordinateSpace.REQUEST_IMAGE_PX.value)),
            )
        except (KeyError, TypeError, ValueError):
            notes.append("Invalid target_region payload.")
            return None

    def _parse_confidence(self, raw_value: Any) -> ConfidenceLevel:
        if isinstance(raw_value, str):
            try:
                return ConfidenceLevel(raw_value)
            except ValueError:
                return ConfidenceLevel.LOW
        return ConfidenceLevel.MEDIUM

    def _string_or_default(self, raw_value: Any, default: str) -> str:
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
        return default

    def _optional_string(self, raw_value: Any) -> Optional[str]:
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value
        return None
