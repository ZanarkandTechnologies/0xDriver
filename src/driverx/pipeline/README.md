# Pipeline

## Purpose

Coordinate complete scene and batch runs across loader, reasoner, planner,
evaluator, renderer, and submission packager.

## Public API

- `inspect_scene(config)`
- `run_scene(config)`
- `run_batch(config, fixture_names)`

## Minimal Example

```python
from driverx.core.config import load_config
from driverx.pipeline.scene_run import run_scene

result = run_scene(load_config("configs/mock.yaml"))
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock tests.test_batch
```
