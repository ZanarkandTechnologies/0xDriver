"""Deterministic mock reasoner for local proof runs."""

from __future__ import annotations

from driverx.core.types import DrivingIntent, FrameBundle
from driverx.reasoning.schema import intent_from_mapping


class MockReasoner:
    def __init__(self, default_uncertainty: float = 0.34) -> None:
        self.default_uncertainty = default_uncertainty

    def infer_intent(self, frame: FrameBundle) -> DrivingIntent:
        scenario = str(frame.metadata.get("scenario", "unknown"))
        hazards = [str(item) for item in frame.metadata.get("hazards", [])]
        if scenario == "construction_merge":
            payload = {
                "scene_type": "construction work-zone merge",
                "hazards": hazards,
                "ego_intent": "continue while slowing for work-zone constraints",
                "target_behavior": "yield_then_proceed",
                "speed_profile": "decelerate_then_creep",
                "lateral_bias": "right",
                "uncertainty": self.default_uncertainty,
            }
        elif scenario == "straight_clear":
            payload = {
                "scene_type": "clear straight road",
                "hazards": hazards,
                "ego_intent": "continue in lane",
                "target_behavior": "proceed",
                "speed_profile": "steady",
                "lateral_bias": "center",
                "uncertainty": min(self.default_uncertainty, 0.18),
            }
        else:
            payload = {
                "scene_type": "unknown scene",
                "hazards": hazards,
                "ego_intent": "fallback to cautious stop",
                "target_behavior": "stop",
                "speed_profile": "brake",
                "lateral_bias": "center",
                "uncertainty": 0.9,
            }
        return intent_from_mapping(payload)
