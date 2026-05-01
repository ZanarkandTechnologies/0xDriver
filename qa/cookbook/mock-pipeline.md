# Mock Pipeline QA

## Purpose

Proves the first 0xDriver loop without real Waymo data or VLA access.

## Preconditions

- Required data: none.
- Required services: none.
- Required env vars: none.

## Commands

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml --run-id qa-inspect
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id qa-scene
PYTHONPATH=src python3 -m driverx run-scene --config configs/invalid_reasoner.yaml --run-id qa-invalid-reasoner
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml --run-id qa-batch
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
- `submission_shard_00000.pb`
- `submission_schema.proto`
- `batch_summary.json`
- `reasoner_error.json` from the invalid reasoner fallback run

## Failure Notes

- If imports fail, run from the repo root with `PYTHONPATH=src`.
- If a real Waymo config is selected, v1 should fail clearly and recommend the
  fixture path.
