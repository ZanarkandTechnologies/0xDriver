"""Trajectory smoothing and continuity clamps."""

from __future__ import annotations

import math

from driverx.core.types import Point, TrajectoryCandidate


def _clamp_step(previous: Point, current: Point, max_step: float) -> Point:
    px, py = previous
    cx, cy = current
    dx = cx - px
    dy = cy - py
    distance = math.hypot(dx, dy)
    if distance <= max_step or distance == 0:
        return current
    scale = max_step / distance
    return px + dx * scale, py + dy * scale


def smooth_candidate(candidate: TrajectoryCandidate, max_step: float = 1.25) -> TrajectoryCandidate:
    smoothed: list[Point] = []
    for point in candidate.points_xy:
        if not smoothed:
            smoothed.append(point)
            continue
        clamped = _clamp_step(smoothed[-1], point, max_step=max_step)
        blended = (
            smoothed[-1][0] * 0.15 + clamped[0] * 0.85,
            smoothed[-1][1] * 0.15 + clamped[1] * 0.85,
        )
        smoothed.append((round(blended[0], 4), round(blended[1], 4)))
    return TrajectoryCandidate(
        points_xy=smoothed,
        source=f"{candidate.source}_smooth",
        score=candidate.score,
        metadata={**candidate.metadata, "smoothed": True, "max_step": max_step},
    )
