import unittest

from driverx.reasoning.schema import intent_from_mapping


class ReasoningSchemaTest(unittest.TestCase):
    def test_valid_intent_mapping(self) -> None:
        intent = intent_from_mapping(
            {
                "scene_type": "construction",
                "hazards": ["cones"],
                "ego_intent": "slow",
                "target_behavior": "yield_then_proceed",
                "speed_profile": "decelerate_then_creep",
                "lateral_bias": "right",
                "uncertainty": 0.4,
            }
        )
        self.assertEqual(intent.lateral_bias, "right")
        self.assertEqual(intent.hazards, ["cones"])

    def test_invalid_hazards_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            intent_from_mapping(
                {
                    "scene_type": "construction",
                    "hazards": "cones",
                    "ego_intent": "slow",
                    "target_behavior": "yield_then_proceed",
                    "speed_profile": "decelerate_then_creep",
                    "lateral_bias": "right",
                    "uncertainty": 0.4,
                }
            )

    def test_invalid_lateral_bias_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            intent_from_mapping(
                {
                    "scene_type": "construction",
                    "hazards": [],
                    "ego_intent": "slow",
                    "target_behavior": "yield_then_proceed",
                    "speed_profile": "decelerate_then_creep",
                    "lateral_bias": "diagonal",
                    "uncertainty": 0.4,
                }
            )


if __name__ == "__main__":
    unittest.main()
