"""Small timing helper for pipeline stage accounting."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterator


@dataclass
class StageTimer:
    timings_ms: dict[str, float] = field(default_factory=dict)

    @contextmanager
    def track(self, stage: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (perf_counter() - start) * 1000.0
            self.timings_ms[stage] = self.timings_ms.get(stage, 0.0) + elapsed_ms
