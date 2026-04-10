from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional
from uuid import uuid4

import mss
from PIL import Image, ImageDraw

from .models import CaptureMetadata, DisplayMonitor, GuidedAction, Point2D, utc_now_iso


class CaptureService:
    def capture_full_desktop(
        self,
        image_path: Path,
        debug_image_path: Optional[Path] = None,
        guided_action: Optional[GuidedAction] = None,
    ) -> CaptureMetadata:
        image_path.parent.mkdir(parents=True, exist_ok=True)
        if debug_image_path is not None:
            debug_image_path.parent.mkdir(parents=True, exist_ok=True)

        with mss.mss() as sct:
            virtual_monitor = sct.monitors[0]
            shot = sct.grab(virtual_monitor)
            image = Image.frombytes("RGB", shot.size, shot.rgb)
            image.save(image_path, format="PNG")

            monitors = [
                DisplayMonitor(
                    left=int(monitor["left"]),
                    top=int(monitor["top"]),
                    width=int(monitor["width"]),
                    height=int(monitor["height"]),
                )
                for monitor in sct.monitors[1:]
            ]

        if debug_image_path is not None and guided_action is not None:
            self._save_debug_image(image, debug_image_path, guided_action, virtual_monitor["left"], virtual_monitor["top"])

        return CaptureMetadata(
            capture_id=str(uuid4()),
            created_at=utc_now_iso(),
            image_path=str(image_path),
            debug_image_path=str(debug_image_path) if debug_image_path is not None else None,
            virtual_left=int(virtual_monitor["left"]),
            virtual_top=int(virtual_monitor["top"]),
            capture_width=int(virtual_monitor["width"]),
            capture_height=int(virtual_monitor["height"]),
            request_width=int(image.width),
            request_height=int(image.height),
            monitors=monitors,
        )

    def encode_image_data_url(self, image_path: Path) -> str:
        raw = image_path.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def annotate_capture(
        self,
        image_path: Path,
        debug_image_path: Path,
        guided_action: GuidedAction,
        capture: CaptureMetadata,
    ) -> None:
        image = Image.open(image_path).convert("RGB")
        self._save_debug_image(
            image=image,
            debug_image_path=debug_image_path,
            guided_action=guided_action,
            virtual_left=capture.virtual_left,
            virtual_top=capture.virtual_top,
        )

    def _save_debug_image(
        self,
        image: Image.Image,
        debug_image_path: Path,
        guided_action: GuidedAction,
        virtual_left: int,
        virtual_top: int,
    ) -> None:
        debug_image = image.copy()
        draw = ImageDraw.Draw(debug_image)
        point = guided_action.mapped_screen_point

        if point is not None:
            local_x = int(round(point.x - virtual_left))
            local_y = int(round(point.y - virtual_top))
            radius = 18
            draw.ellipse(
                (local_x - radius, local_y - radius, local_x + radius, local_y + radius),
                outline=(255, 64, 64),
                width=3,
            )
            draw.line((local_x - 24, local_y, local_x + 24, local_y), fill=(255, 64, 64), width=2)
            draw.line((local_x, local_y - 24, local_x, local_y + 24), fill=(255, 64, 64), width=2)

        debug_image.save(debug_image_path, format="PNG")
