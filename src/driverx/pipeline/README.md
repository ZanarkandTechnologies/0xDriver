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

## Minimal Example

```python
from driverx.core.config import load_config
from driverx.pipeline import run_batch, run_experiment, run_scene

result = run_scene(load_config("configs/mock.yaml"))
batch = run_batch(load_config("configs/mock.yaml"))
experiment = run_experiment(load_config("configs/mock.yaml"))
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_pipeline_mock tests.test_batch
```
