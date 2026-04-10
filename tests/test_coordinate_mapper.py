import unittest

from aiclickhelper.coordinate_mapper import CoordinateMapper
from aiclickhelper.models import (
    ActionType,
    CaptureMetadata,
    ConfidenceLevel,
    CoordinateSpace,
    DisplayMonitor,
    GuidedAction,
    Point2D,
)


class CoordinateMapperTests(unittest.TestCase):
    def test_maps_request_image_point_to_absolute_screen(self):
        mapper = CoordinateMapper()
        capture = CaptureMetadata(
            capture_id="cap-1",
            created_at="2026-01-01T00:00:00+00:00",
            image_path="capture.png",
            debug_image_path=None,
            virtual_left=-1920,
            virtual_top=0,
            capture_width=3840,
            capture_height=2160,
            request_width=1920,
            request_height=1080,
            monitors=[DisplayMonitor(left=-1920, top=0, width=1920, height=1080)],
        )
        action = GuidedAction(
            action_id="a1",
            step_index=1,
            source_response_id="resp-1",
            action_type=ActionType.CLICK,
            explanation="test",
            expected_next_state="test",
            user_instruction="test",
            confidence=ConfidenceLevel.HIGH,
            advisory_only=False,
            executable=False,
            target_point=Point2D(x=960, y=540, coord_space=CoordinateSpace.REQUEST_IMAGE_PX),
        )

        mapped = mapper.map_action(action, capture)
        self.assertIsNotNone(mapped.mapped_screen_point)
        self.assertEqual(mapped.mapped_screen_point.x, 0.0)
        self.assertEqual(mapped.mapped_screen_point.y, 1080.0)


if __name__ == "__main__":
    unittest.main()
