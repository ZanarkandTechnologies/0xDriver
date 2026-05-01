"""Validation helpers for structured VLA/VLM intent."""

from __future__ import annotations

from typing import Any, Literal, get_args

from driverx.core.types import DrivingIntent

LateralBias = Literal["left", "center", "right"]


def intent_from_mapping(payload: dict[str, Any]) -> DrivingIntent:
    hazards_raw = payload.get("hazards", [])
    if not isinstance(hazards_raw, list) or not all(
        isinstance(item, str) for item in hazards_raw
    ):
        raise ValueError("Driving intent 'hazards' must be a list of strings.")

    lateral_bias = str(payload.get("lateral_bias", "center"))
    if lateral_bias not in get_args(LateralBias):
        raise ValueError("Driving intent lateral_bias must be left, center, or right.")

    return DrivingIntent(
        scene_type=str(payload.get("scene_type", "")),
        hazards=hazards_raw,
        ego_intent=str(payload.get("ego_intent", "")),
        target_behavior=str(payload.get("target_behavior", "")),
        speed_profile=str(payload.get("speed_profile", "")),
        lateral_bias=lateral_bias,  # type: ignore[arg-type]
        uncertainty=float(payload.get("uncertainty", 1.0)),
    )
