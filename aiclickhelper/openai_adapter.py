from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .config import AppConfig
from .models import CaptureMetadata, ChatMessage, GuidedAction, SessionData, Speaker


class OpenAIAdapter:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "paste_your_openai_api_key_here":
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Put it in .env or the process environment."
            )
        self._client = OpenAI(
            api_key=api_key,
            timeout=float(config.openai_timeout_seconds),
        )

    def request_guided_action(
        self,
        session: SessionData,
        new_prompt: str,
        screenshot_data_url: str,
    ) -> tuple[str, str]:
        request = self._build_request(session, new_prompt, screenshot_data_url)
        response = self._client.responses.create(**request)

        response_id = getattr(response, "id", "")
        assistant_text = self.extract_assistant_text(response)
        return response_id, assistant_text

    def _build_request(
        self,
        session: SessionData,
        new_prompt: str,
        screenshot_data_url: str,
    ) -> dict[str, Any]:
        # The app owns a compact JSON contract so the UI is insulated from
        # raw model/tool payload changes.
        operator_context = self._format_recent_context(session)
        instructions = (
            "You are a Windows GUI operator assistant. "
            "Recommend exactly one next step at a time based on the screenshot and session context. "
            "No matter which application, dialog, or window is currently visible, your job is to help complete the operator's requested task inside the real target UI. "
            "Do not get distracted by the assistant window, overlays, prior guesses, or unrelated visible content. "
            "Treat every turn as a fresh inspection of the current screen state and rebuild your understanding from the screenshot before choosing the next action. "
            "Infer a practical step-by-step algorithm for the task, follow it consistently, and choose the single highest-value next action that advances the task. "
            "Do not suggest interacting with the assistant window itself unless the operator explicitly asked for that. "
            "Do not claim the action was executed. "
            "Return only valid JSON with this shape: "
            "{\"action_type\": str, "
            "\"target_point\": {\"x\": number, \"y\": number, \"coord_space\": \"request_image_px\"} or null, "
            "\"target_region\": {\"left\": number, \"top\": number, \"width\": number, \"height\": number, \"coord_space\": \"request_image_px\"} or null, "
            "\"explanation\": str, "
            "\"expected_next_state\": str, "
            "\"user_instruction\": str, "
            "\"input_text\": str or null, "
            "\"confidence\": \"high\"|\"medium\"|\"low\", "
            "\"advisory_only\": boolean, "
            "\"executable\": boolean}. "
            "Use request_image_px coordinates relative to the screenshot image exactly as provided. "
            "If you are unsure, return action_type 'ask_user' or 'blocked' with no coordinates. "
            "Prefer concise explanation and expected_next_state strings."
        )

        input_items = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": operator_context},
                    {"type": "input_text", "text": f"Latest operator message:\n{new_prompt}"},
                    {
                        "type": "input_image",
                        "image_url": screenshot_data_url,
                        "detail": "original",
                    },
                ],
            }
        ]

        request: dict[str, Any] = {
            "model": session.model or self._config.model,
            "instructions": instructions,
            "input": input_items,
            "reasoning": {"effort": "low"},
            "truncation": "auto",
        }
        if session.previous_response_id:
            request["previous_response_id"] = session.previous_response_id
        return request

    def _format_recent_context(self, session: SessionData) -> str:
        lines: list[str] = [
            f"Session step index: {session.step_index}",
            "Use the screenshot as the source of truth for the current UI state.",
        ]
        if session.summary.strip():
            lines.append(f"Rolling summary: {session.summary.strip()}")

        recent_messages = session.history[-6:]
        if recent_messages:
            lines.append("Recent conversation:")
            for message in recent_messages:
                lines.append(f"- {message.speaker.value}: {message.text}")

        recent_actions = session.actions[-3:]
        if recent_actions:
            lines.append("Recent recommended actions:")
            for action in recent_actions:
                lines.append(
                    f"- step {action.step_index}: {action.action_type.value}; expected={action.expected_next_state}"
                )

        return "\n".join(lines)

    def extract_assistant_text(self, response: Any) -> str:
        output = getattr(response, "output", None) or []
        parts: list[str] = []
        for item in output:
            if getattr(item, "type", None) != "message":
                continue
            content = getattr(item, "content", None) or []
            for part in content:
                part_type = getattr(part, "type", None)
                if part_type in {"output_text", "text"}:
                    text = getattr(part, "text", None)
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
        if parts:
            return "\n\n".join(parts)
        try:
            return json.dumps(response.model_dump(), indent=2)
        except Exception:
            return str(response)
