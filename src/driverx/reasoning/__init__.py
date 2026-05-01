"""Reasoning backend selection."""

from driverx.core.config import ReasonerConfig
from driverx.reasoning.base import Reasoner
from driverx.reasoning.mock import InvalidMockReasoner, MockReasoner


def build_reasoner(config: ReasonerConfig) -> Reasoner:
    if config.backend == "mock":
        return MockReasoner(default_uncertainty=config.uncertainty)
    if config.backend == "invalid_mock":
        return InvalidMockReasoner()
    raise ValueError(
        f"Unsupported reasoner backend '{config.backend}'. "
        "Only 'mock' is available in v1."
    )


__all__ = ["Reasoner", "InvalidMockReasoner", "MockReasoner", "build_reasoner"]
