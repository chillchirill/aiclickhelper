from __future__ import annotations

from dataclasses import replace
from typing import Optional

from .models import CaptureMetadata, CoordinateSpace, GuidedAction, Point2D, Region2D


class CoordinateMapper:
    def map_action(self, action: GuidedAction, capture: CaptureMetadata) -> GuidedAction:
        notes = list(action.validation_notes)
        mapped_point: Optional[Point2D] = None

        point = action.target_point or self._region_center(action.target_region)
        if point is None:
            notes.append("No target point or target region was provided by the model.")
            return replace(action, validation_notes=notes, advisory_only=True, executable=False)

        request_x, request_y = self._to_request_space(point, capture)
        if request_x is None or request_y is None:
            notes.append(f"Unsupported coordinate space for target point: {point.coord_space}.")
            return replace(action, validation_notes=notes, advisory_only=True, executable=False)

        if not (0 <= request_x <= capture.request_width and 0 <= request_y <= capture.request_height):
            notes.append("Target coordinates were outside the submitted screenshot bounds.")
            return replace(action, validation_notes=notes, advisory_only=True, executable=False)

        # Convert from request-image pixels to absolute virtual-desktop pixels.
        screen_x = capture.virtual_left + round(request_x * capture.capture_width / capture.request_width)
        screen_y = capture.virtual_top + round(request_y * capture.capture_height / capture.request_height)
        mapped_point = Point2D(
            x=float(screen_x),
            y=float(screen_y),
            coord_space=CoordinateSpace.DESKTOP_ABS_PX,
        )
        return replace(action, mapped_screen_point=mapped_point, validation_notes=notes)

    def _region_center(self, region: Optional[Region2D]) -> Optional[Point2D]:
        if region is None:
            return None
        return Point2D(
            x=region.left + (region.width / 2.0),
            y=region.top + (region.height / 2.0),
            coord_space=region.coord_space,
        )

    def _to_request_space(self, point: Point2D, capture: CaptureMetadata) -> tuple[Optional[float], Optional[float]]:
        if point.coord_space == CoordinateSpace.REQUEST_IMAGE_PX:
            return point.x, point.y
        if point.coord_space == CoordinateSpace.NORMALIZED:
            return point.x * capture.request_width, point.y * capture.request_height
        if point.coord_space == CoordinateSpace.CAPTURE_ABS_PX:
            return point.x - capture.virtual_left, point.y - capture.virtual_top
        if point.coord_space == CoordinateSpace.DESKTOP_ABS_PX:
            return point.x - capture.virtual_left, point.y - capture.virtual_top
        return None, None
