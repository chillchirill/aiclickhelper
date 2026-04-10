import unittest

from aiclickhelper.models import ActionType
from aiclickhelper.response_normalizer import ResponseNormalizer


class ResponseNormalizerTests(unittest.TestCase):
    def test_normalizes_valid_json_response(self):
        normalizer = ResponseNormalizer()
        text = """
        {
          "action_type": "click",
          "target_point": {"x": 100, "y": 200, "coord_space": "request_image_px"},
          "target_region": null,
          "explanation": "Open the File menu.",
          "expected_next_state": "The menu opens.",
          "user_instruction": "Click the File button.",
          "input_text": null,
          "confidence": "high",
          "advisory_only": true,
          "executable": false
        }
        """
        action = normalizer.normalize("resp-1", 1, text)
        self.assertEqual(action.action_type, ActionType.CLICK)
        self.assertEqual(action.target_point.x, 100)
        self.assertFalse(action.is_terminal)

    def test_falls_back_to_blocked_for_non_json_text(self):
        normalizer = ResponseNormalizer()
        action = normalizer.normalize("resp-2", 2, "just do something")
        self.assertEqual(action.action_type, ActionType.BLOCKED)
        self.assertTrue(action.is_terminal)
        self.assertTrue(action.validation_notes)


if __name__ == "__main__":
    unittest.main()
