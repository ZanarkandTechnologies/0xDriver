# Mock Pipeline QA

## Purpose

Proves the first 0xDriver loop without real Waymo data or VLA access.

## Preconditions

- Required data: none.
- Required services: none.
- Required env vars: none.

## Commands

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Expected Evidence

- `scene_inspection.svg`
- `scene_prediction.svg`
- `intent.json`
- `selected_trajectory.json`
- `metrics.json`
- `timings.json`
- `submission_dry_run.json`
- `batch_summary.json`

## Failure Notes

- If imports fail, run from the repo root with `PYTHONPATH=src`.
- If a real Waymo config is selected, v1 should fail clearly and recommend the
  fixture path.
