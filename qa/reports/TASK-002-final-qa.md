# TASK-002 Final QA

## Verdict

TASK-002 passes all stated acceptance criteria.

## Acceptance Criteria

### AC-1: Waymo JSON Fixture Still Loads Without TensorFlow

Status: PASS.

Evidence:

- `src/driverx/datasets/waymo_e2e.py` routes `.json` paths to the fixture loader
  before importing TensorFlow or Waymo modules.
- `tests/test_waymo_loader.py` covers the JSON fixture path.
- `driverx inspect-scene --config configs/waymo_fixture.yaml` produced
  `artifacts/runs/task2-waymo-fixture-r2/scene_inspection.svg`.

### AC-2: TFRecord Path/Glob/Directory Attempts Optional Official Parsing

Status: PASS.

Evidence:

- `src/driverx/datasets/waymo_e2e.py` expands file, directory, and glob inputs.
- `tests/test_waymo_loader.py` covers TFRecord dependency boundaries and
  multi-shard provenance.
- A throwaway empty TFRecord reached the optional dependency boundary and exited
  with setup guidance.

### AC-3: Missing Optional Dependencies Fail Clearly

Status: PASS.

Evidence:

- Loader and packager wrap missing modules in operator-facing errors.
- CLI catches `ImportError`, `FileNotFoundError`, `IndexError`, and `ValueError`
  as `driverx error:` messages.
- `tests/test_cli.py` confirms official-packaging missing deps produce no
  traceback.

### AC-4: Official Packaging Uses Official Protobufs When Present

Status: PASS.

Evidence:

- `src/driverx/submission/waymo_packager.py` imports the official submission
  protobuf module only when `official=True`.
- `tests/test_submission_packager.py` verifies the positive path with a fake
  Waymo module, validates required metadata, and checks missing-dependency
  behavior.

### AC-5: Default Mock Pipeline Still Passes Without Optional Deps

Status: PASS.

Evidence:

- `bash scripts/pre_push_check.sh`: PASS, 28 tests.
- `driverx run-scene --config configs/mock.yaml --run-id task2-mock-run-r2`
  produced normal metrics and packaging artifacts.

### AC-6: README Documents Real Validation Setup

Status: PASS.

Evidence:

- `README.md` documents `python -m pip install ".[waymo]"`,
  `WAYMO_E2E_TFRECORD`, `configs/waymo_local.sample.yaml`, and required
  `--official` metadata fields.

## Commands

- `bash scripts/pre_push_check.sh`
- `PYTHONPATH=src python3 -m driverx show-config --config configs/waymo_local.sample.yaml`
- `PYTHONPATH=src python3 -m driverx inspect-scene --config configs/waymo_fixture.yaml --run-id task2-waymo-fixture-r2`
- `PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id task2-mock-run-r2`
- `PYTHONPATH=src python3 -m driverx package-submission --run-dir artifacts/runs/task2-mock-run-r2 --official`
- `WAYMO_E2E_TFRECORD=/tmp/driverx_empty_waymo.tfrecord PYTHONPATH=src python3 -m driverx inspect-scene --config configs/waymo_local.sample.yaml`

## Artifacts

- Waymo fixture inspection: `artifacts/runs/task2-waymo-fixture-r2/scene_inspection.svg`
- Mock prediction: `artifacts/runs/task2-mock-run-r2/scene_prediction.svg`
- Mock metrics: `artifacts/runs/task2-mock-run-r2/metrics.json`
- Dry-run submission JSON: `artifacts/runs/task2-mock-run-r2/submission_dry_run.json`
- Local protobuf shard: `artifacts/runs/task2-mock-run-r2/submission_shard_00000.pb`

## Residual Caveats

- Real TFRecord validation still requires the user to download a Waymo E2E shard
  and install optional Waymo/TensorFlow packages.
- Typecheck and build are skipped by `scripts/pre_push_check.sh` because this
  repo currently has no configured typecheck/build command.
