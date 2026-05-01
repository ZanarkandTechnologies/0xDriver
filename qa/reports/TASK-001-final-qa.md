# TASK-001 Final QA Report

- QA date: 2026-05-02
- Scope: fixture-backed offline 0xDriver pipeline
- Verdict: PASS for v1 fixture/mock scope

## Commands Run

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml --run-id final-qa2-inspect
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/waymo_fixture.yaml --run-id final-qa2-waymo-fixture
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id final-qa2-scene
PYTHONPATH=src python3 -m driverx evaluate --run-dir artifacts/runs/final-qa2-scene
PYTHONPATH=src python3 -m driverx package-submission --run-dir artifacts/runs/final-qa2-scene
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml --run-id final-qa2-batch
PYTHONPATH=src python3 -m driverx run-scene --config configs/invalid_reasoner.yaml --run-id final-qa2-invalid
bash scripts/pre_push_check.sh
```

## Evidence Artifacts

- Inspect scene: `artifacts/runs/final-qa2-inspect/scene_inspection.svg`
- Waymo-shaped fixture inspect scene: `artifacts/runs/final-qa2-waymo-fixture/scene_inspection.svg`
- Predicted scene: `artifacts/runs/final-qa2-scene/scene_prediction.svg`
- Intent: `artifacts/runs/final-qa2-scene/intent.json`
- Raw candidates: `artifacts/runs/final-qa2-scene/raw_candidates.json`
- Smoothed candidates: `artifacts/runs/final-qa2-scene/smoothed_candidates.json`
- Selected trajectory: `artifacts/runs/final-qa2-scene/selected_trajectory.json`
- Metrics: `artifacts/runs/final-qa2-scene/metrics.json`
- Timings: `artifacts/runs/final-qa2-scene/timings.json`
- Submission dry-run JSON: `artifacts/runs/final-qa2-scene/submission_dry_run.json`
- Submission protobuf shard: `artifacts/runs/final-qa2-scene/submission_shard_00000.pb`
- Submission protobuf schema: `artifacts/runs/final-qa2-scene/submission_schema.proto`
- Batch summary: `artifacts/runs/final-qa2-batch/batch_summary.json`
- Invalid reasoner fallback: `artifacts/runs/final-qa2-invalid/reasoner_error.json`

## Results

- Single-scene ADE: `0.779339`
- Batch scenes: `2`
- Batch mean ADE: `0.472727`
- Invalid reasoner fallback ADE: `4.837193` (intentional failure case)
- Tests: `19` unittest cases passed
- Local gate: `bash scripts/pre_push_check.sh` passed

## User Story Reconciliation

### US-001: Load And Inspect Waymo E2E Scenes

Status: PASS within fixture-backed v1 scope.

- A documented command loads a configured fixture frame.
- A documented `dataset.kind=waymo` command loads a Waymo E2E-shaped local
  fixture frame from `tests/fixtures/waymo_e2e_frame.json`.
- Front-left, front, and front-right camera panels render in
  `scene_inspection.svg`.
- Fixture future waypoints are overlaid in the top-down evidence panel.
- Real Waymo mode fails clearly as a future optional dependency path.

### US-002: Produce Structured VLA Driving Intent

Status: PASS.

- Mock reasoner emits validated structured JSON fields.
- Invalid hazard and lateral-bias schema cases fail closed in tests.
- Invalid runtime reasoner output records `reasoner_error.json` and falls back
  to a safe-stop intent.
- Raw intent is saved to `intent.json`.

### US-003: Generate And Smooth Trajectory Candidates

Status: PASS.

- Raw candidates and smoothed candidates are saved separately.
- Each candidate and selected trajectory contains exactly 20 `(x, y)` points.
- Smoothing clamp behavior is covered by tests.
- Fallback and cautious candidates exist alongside the intent-primary candidate.

### US-004: Evaluate And Package Submission Artifacts

Status: PASS for v1 package scope.

- ADE is computed for the single-scene run and two-scene batch.
- Dry-run Waymo-style submission JSON, a binary protobuf shard, and the local
  dry-run protobuf schema are created.
- Timings separate load, reason, generate, smooth, rank, evaluate, render, and
  package stages.
- Failure case: `configs/invalid_reasoner.yaml` simulates malformed model
  output. The pipeline records the validation error and falls back to a safe
  stop trajectory. This deliberately produces worse ADE (`4.837193`) than the
  nominal planner, which is expected because the behavior prioritizes safety
  over matching the fixture future trajectory.

## Residual Risks

- Real Waymo TFRecord parsing is still intentionally unimplemented.
- The protobuf shard uses a local dry-run schema, not the official Waymo
  challenge protobuf schema.
- Mock VLA intent is deterministic and does not prove real model quality.
- No cloud GPU backend exists yet.
