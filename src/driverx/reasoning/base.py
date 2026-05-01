"""Reasoner protocol."""

from __future__ import annotations

from typing import Protocol

from driverx.core.types import DrivingIntent, FrameBundle


class Reasoner(Protocol):
    def infer_intent(self, frame: FrameBundle) -> DrivingIntent:
        """Infer structured driving intent from a frame."""
