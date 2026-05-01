"""Candidate trajectory generation from ego history and structured intent."""

from __future__ import annotations

from driverx.core.types import DrivingIntent, FrameBundle, Point, TrajectoryCandidate


def _velocity_from_history(history: list[Point]) -> Point:
    (x0, y0), (x1, y1) = history[-2], history[-1]
    return x1 - x0, y1 - y0


def _profile_scale(speed_profile: str, step_index: int) -> float:
    progress = step_index / 19.0
    if speed_profile == "decelerate_then_creep":
        return max(0.45, 0.88 - progress * 0.40)
    if speed_profile == "brake":
        return max(0.05, 0.75 - progress * 0.75)
    if speed_profile == "steady":
        return 1.0
    return 0.72


def _bias_target(lateral_bias: str) -> float:
    if lateral_bias == "left":
        return 0.7
    if lateral_bias == "right":
        return -0.7
    return 0.0


def _make_candidate(
    frame: FrameBundle,
    intent: DrivingIntent,
    source: str,
    lateral_target: float,
    speed_multiplier: float,
) -> TrajectoryCandidate:
    vx, vy = _velocity_from_history(frame.ego_history_xy)
    last_x, last_y = frame.ego_history_xy[-1]
    points: list[Point] = []
    x = last_x
    y = last_y
    for step in range(20):
        scale = _profile_scale(intent.speed_profile, step) * speed_multiplier
        x += max(0.05, vx * scale)
        y += vy * scale
        y += (lateral_target - y) * 0.10
        points.append((round(x, 4), round(y, 4)))
    score = intent.uncertainty
    return TrajectoryCandidate(
        points_xy=points,
        source=source,
        score=score,
        metadata={
            "lateral_target": lateral_target,
            "speed_multiplier": speed_multiplier,
            "target_behavior": intent.target_behavior,
        },
    )


def generate_candidates(frame: FrameBundle, intent: DrivingIntent) -> list[TrajectoryCandidate]:
    target = _bias_target(intent.lateral_bias)
    return [
        _make_candidate(frame, intent, "intent_primary", target, 1.0),
        _make_candidate(frame, intent, "cautious_slow", target * 0.75, 0.72),
        _make_candidate(frame, intent, "fallback_center_brake", 0.0, 0.42),
    ]
