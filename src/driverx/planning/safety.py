"""Simple deterministic trajectory safety scoring."""

from __future__ import annotations

import math
from typing import Any

from driverx.core.types import TrajectoryCandidate


def obstacle_cost(candidate: TrajectoryCandidate, objects: list[dict[str, Any]]) -> float:
    cost = 0.0
    for obj in objects:
        if obj.get("kind") not in {"stopped_vehicle", "cone", "occlusion"}:
            continue
        ox = float(obj.get("x", 0.0))
        oy = float(obj.get("y", 0.0))
        closest = min(math.hypot(px - ox, py - oy) for px, py in candidate.points_xy)
        if closest < 0.75:
            cost += 10.0
        elif closest < 1.5:
            cost += 2.0 * (1.5 - closest)
    return cost


def smoothness_cost(candidate: TrajectoryCandidate) -> float:
    cost = 0.0
    points = candidate.points_xy
    for idx in range(2, len(points)):
        prev_dx = points[idx - 1][0] - points[idx - 2][0]
        prev_dy = points[idx - 1][1] - points[idx - 2][1]
        dx = points[idx][0] - points[idx - 1][0]
        dy = points[idx][1] - points[idx - 1][1]
        cost += math.hypot(dx - prev_dx, dy - prev_dy)
    return cost
