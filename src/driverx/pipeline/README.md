# Pipeline

## Purpose

Coordinate complete scene and batch runs across loader, reasoner, planner,
evaluator, renderer, and submission packager.

## Public API

- `inspect_scene(config)`
- `run_scene(config)`
- `run_loaded_scene(config, frame)`
- `run_batch(config, fixture_names=None, frame_start=None, frame_count=None)`
- `run_experiment(config, frame_start=None, frame_count=None)`
- `run_rag_comparison(policy, fixture, behavior_id, output_root, run_id)`

## Minimal Example

```python
from pathlib import Path

from driverx.core.config import load_config
from driverx.pipeline import run_batch, run_experiment, run_rag_comparison, run_scene

result = run_scene(load_config("configs/mock.yaml"))
batch = run_batch(load_config("configs/mock.yaml"))
experiment = run_experiment(load_config("configs/mock.yaml"))
comparison = run_rag_comparison(
    policy="mock",
    fixture="construction_merge",
    behavior_id="motorcycle_filtering",
    output_root=Path("artifacts/runs"),
    run_id="rag-comparison",
)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock tests.test_batch tests.test_rag_comparison
```
