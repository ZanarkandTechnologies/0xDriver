# TASK-002: Add Optional Real Waymo E2E Integration

## Status

- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-001, docs/prd.md
- location: src/driverx/datasets, src/driverx/submission, configs, tests, docs
- enter when: fixture-backed v1 passes and the next blocker is real Waymo data/protobuf compatibility
- leave when: optional Waymo TFRecord loading and official protobuf packaging paths exist, fail clearly without optional deps, and preserve fixture QA
- blockers: real Waymo sample data is needed only for live-data validation, not for implementation
- spawned follow-ups: none yet
- complexity: M

## Description

TASK-001 proved the pipeline with fixtures and a Waymo-shaped JSON sample. This
ticket turns those seams into real optional integration points: Waymo TFRecord
loading when the official packages are installed, and official
`E2EDChallengeSubmission` serialization when the official protobufs are present.
The default fixture path must remain dependency-free and runnable on the local
MacBook.

## Goal

Make the repo ready for a user-provided Waymo E2E shard without blocking normal
development on large downloads, TensorFlow, or Waymo package availability.

## Plan

### Change

Add optional Waymo dependency detection, TFRecord frame parsing, documented
Waymo config examples, official protobuf submission serialization, and tests for
the optional-dependency/fallback boundaries.

### Why

The next credibility gap is no longer the architecture loop; it is whether the
repo can attach to the official Waymo E2E data/package surfaces without turning
local QA brittle.

### Before -> After

- Before: `dataset.kind=waymo` supports a JSON fixture and otherwise raises a
  placeholder `NotImplementedError`.
- After: `dataset.kind=waymo` can read a real `.tfrecord`/glob/directory when
  Waymo dependencies exist, while missing deps produce install guidance and
  fixture tests stay green.

### Touch

- `pyproject.toml`
- `configs/waymo_local.sample.yaml`
- `src/driverx/core/config.py`
- `src/driverx/datasets/waymo_e2e.py`
- `src/driverx/submission/waymo_packager.py`
- `tests/test_waymo_loader.py`
- `tests/test_submission_packager.py`
- `README.md`
- `docs/progress.md`
- `docs/HISTORY.md`

### Inspect

- `src/driverx/datasets/__init__.py`
- `src/driverx/pipeline/scene_run.py`
- `tests/test_pipeline_mock.py`
- `docs/prd.md`
- `qa/reports/TASK-001-final-qa.md`

### Signature Delta

- `DatasetConfig.frame_index: int`
- `DatasetConfig.limit: int | None`
- `load_waymo_frame(config): FrameBundle`
- `load_waymo_tfrecord_frame(config): FrameBundle`
- `package_run_dir(run_dir, output_path=None, official=False): dict`

### Type Sketch

```python
DatasetConfig(kind, name, path, frame_index, limit)
FrameBundle(frame_name, front_images, ego_history_xy, future_xy, metadata)
SubmissionPackage(path, protobuf_shard, protobuf_schema, official, predictions)
```

### Typed Flow Example

`configs/waymo_local.sample.yaml` sets `dataset.path` to a TFRecord glob and
`frame_index=0`. The loader imports TensorFlow and Waymo protobufs, reads the
first matching record, extracts front-left/front/front-right images, ego history,
and future waypoints, then hands a normal `FrameBundle` to the existing
reasoning/planning/evaluation loop. Packaging writes the existing dry-run JSON
and, when requested, uses the official Waymo submission protobuf class.

### Execution Steps

1. Extend config parsing for `frame_index`, `limit`, and package mode.
2. Implement optional Waymo dependency import helpers with actionable errors.
3. Implement TFRecord path expansion for file, directory, and glob inputs.
4. Parse E2E frames into `FrameBundle` using the official proto field names from
   the tutorial.
5. Add official protobuf packaging behind an explicit flag.
6. Add tests for JSON fixture continuity, missing dependency guidance, and
   packager mode selection.
7. Update README/progress/history with the new workflow and remaining data
   blocker.
8. Run tests, review, and commit modularly.

## Acceptance Criteria

- [x] `dataset.kind=waymo` still loads the JSON fixture without TensorFlow.
- [x] A TFRecord path/glob/directory attempts real Waymo parsing through optional
  official dependencies.
- [x] Missing optional dependencies fail with a clear install command and no
  stack-trace mystery.
- [x] `package-submission --official` uses official Waymo protobufs when present
  and fails clearly otherwise.
- [x] Default mock pipeline tests still pass with no optional Waymo deps.
- [x] README documents what the user must download/configure for real validation.

## Evidence Checklist

- [x] Unit tests for loader and packager optional paths.
- [x] `bash scripts/pre_push_check.sh` output.
- [x] Waymo fixture smoke artifact.
- [ ] Review result linked.

## Build Notes

Starting from TASK-001 fixture-backed v1. Real Waymo data is not committed and
is not required for local CI.

Implemented in modular commits:

- `445535e docs(ticket): start waymo integration task`
- `b8a0046 feat(waymo): add optional e2e integration`

Fresh validation:

- `bash scripts/pre_push_check.sh`: PASS, 24 tests.
- `driverx inspect-scene --config configs/waymo_fixture.yaml --run-id task2-waymo-fixture`: PASS.
- `driverx run-scene --config configs/mock.yaml --run-id task2-mock-run`: PASS, ADE `0.779339`.
- `driverx package-submission --run-dir artifacts/runs/task2-mock-run --official`: expected setup failure, clean `driverx error:` message, exit code `2`.
- `WAYMO_E2E_TFRECORD=/tmp/driverx_empty_waymo.tfrecord driverx inspect-scene --config configs/waymo_local.sample.yaml`: expected setup failure, clean `driverx error:` message, exit code `2`.

## QA Reconciliation

- AC-1: PASS
- AC-2: PASS
- AC-3: PASS
- AC-4: PASS

## Artifact Links

- Waymo fixture inspect artifact: `artifacts/runs/task2-waymo-fixture/scene_inspection.svg`
- Mock run prediction artifact: `artifacts/runs/task2-mock-run/scene_prediction.svg`
- Mock run metrics: `artifacts/runs/task2-mock-run/metrics.json`
- Mock run submission dry-run: `artifacts/runs/task2-mock-run/submission_dry_run.json`
- Mock run local protobuf shard: `artifacts/runs/task2-mock-run/submission_shard_00000.pb`
- Review result: pending.

## User Evidence

- Hero artifact: `artifacts/runs/task2-mock-run/scene_prediction.svg`
- Supporting evidence: `artifacts/runs/task2-waymo-fixture/scene_inspection.svg`
- QA report: pending final QA lane.
- Final verdict: implementation checks pass; review/QA pending.

## Required Evidence

- [x] Unit/integration/e2e tests pass as applicable.
- [x] Typecheck/lint gate passes through `scripts/pre_push_check.sh`.
