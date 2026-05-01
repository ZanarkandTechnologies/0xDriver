# Core

## Purpose

Shared typed objects, config loading, artifact helpers, and timing utilities.

## Public API

- `types.py`: `FrameBundle`, `DrivingIntent`, `TrajectoryCandidate`, `SceneRunResult`
- `config.py`: `load_config`
- `artifacts.py`: JSON artifact and run-directory helpers
- `timing.py`: stage latency accounting

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_config
```
