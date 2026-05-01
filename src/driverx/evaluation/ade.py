"""Average displacement error metric."""

from __future__ import annotations

import math

from driverx.core.types import Point


def average_displacement_error(prediction: list[Point], ground_truth: list[Point]) -> float:
    if len(prediction) != len(ground_truth):
        raise ValueError("Prediction and ground truth must have equal length.")
    if not prediction:
        raise ValueError("Prediction must include at least one point.")
    total = 0.0
    for (px, py), (gx, gy) in zip(prediction, ground_truth, strict=True):
        total += math.hypot(px - gx, py - gy)
    return total / len(prediction)
