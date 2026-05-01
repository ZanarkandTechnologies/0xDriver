# driverx

## Purpose

`driverx` is the runtime package for the 0xDriver minimal-shot autonomy
prototype. It keeps fixture data, reasoning, planning, evaluation, visualization,
and submission packaging behind narrow seams.

## Public Entrypoints

- `python3 -m driverx inspect-scene --config configs/mock.yaml`
- `python3 -m driverx run-scene --config configs/mock.yaml`
- `python3 -m driverx run-batch --config configs/mock.yaml`
- `python3 -m driverx evaluate --run-dir <run-dir>`
- `python3 -m driverx package-submission --run-dir <run-dir>`

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
