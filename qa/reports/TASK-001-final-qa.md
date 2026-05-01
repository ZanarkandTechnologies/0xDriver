# TASK-001 Final QA Report

- QA date: 2026-05-02
- Scope: fixture-backed offline 0xDriver pipeline
- Verdict: PASS for v1 fixture/mock scope

## Commands Run

```bash
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml --run-id final-qa-inspect
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml --run-id final-qa-scene
PYTHONPATH=src python3 -m driverx evaluate --run-dir artifacts/runs/final-qa-scene
PYTHONPATH=src python3 -m driverx package-submission --run-dir artifacts/runs/final-qa-scene
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml --run-id final-qa-batch
bash scripts/pre_push_check.sh
```

## Evidence Artifacts

- Inspect scene: `artifacts/runs/final-qa-inspect/scene_inspection.svg`
- Predicted scene: `artifacts/runs/final-qa-scene/scene_prediction.svg`
- Intent: `artifacts/runs/final-qa-scene/intent.json`
- Raw candidates: `artifacts/runs/final-qa-scene/raw_candidates.json`
- Smoothed candidates: `artifacts/runs/final-qa-scene/smoothed_candidates.json`
- Selected trajectory: `artifacts/runs/final-qa-scene/selected_trajectory.json`
- Metrics: `artifacts/runs/final-qa-scene/metrics.json`
- Timings: `artifacts/runs/final-qa-scene/timings.json`
- Submission dry-run: `artifacts/runs/final-qa-scene/submission_dry_run.json`
- Batch summary: `artifacts/runs/final-qa-batch/batch_summary.json`

## Results

- Single-scene ADE: `0.779339`
- Batch scenes: `2`
- Batch mean ADE: `0.472727`
- Tests: `14` unittest cases passed
- Local gate: `bash scripts/pre_push_check.sh` passed

## User Story Reconciliation

### US-001: Load And Inspect Waymo E2E Scenes

Status: PASS within fixture-backed v1 scope.

- A documented command loads a configured fixture frame.
- Front-left, front, and front-right camera panels render in
  `scene_inspection.svg`.
- Fixture future waypoints are overlaid in the top-down evidence panel.
- Real Waymo mode fails clearly as a future optional dependency path.

### US-002: Produce Structured VLA Driving Intent

Status: PASS.

- Mock reasoner emits validated structured JSON fields.
- Invalid hazard and lateral-bias schema cases fail closed in tests.
- Raw intent is saved to `intent.json`.

### US-003: Generate And Smooth Trajectory Candidates

Status: PASS.

- Raw candidates and smoothed candidates are saved separately.
- Each candidate and selected trajectory contains exactly 20 `(x, y)` points.
- Smoothing clamp behavior is covered by tests.
- Fallback and cautious candidates exist alongside the intent-primary candidate.

### US-004: Evaluate And Package Submission Artifacts

Status: PASS for dry-run package scope.

- ADE is computed for the single-scene run and two-scene batch.
- Dry-run Waymo-style submission JSON is created.
- Timings separate load, reason, generate, smooth, rank, evaluate, render, and
  package stages.
- Failure-case analysis is not yet a narrative notebook; it remains a follow-up
  once real Waymo scenes are available.

## Residual Risks

- Real Waymo TFRecord parsing is still intentionally unimplemented.
- Dry-run submission is JSON, not official protobuf serialization.
- Mock VLA intent is deterministic and does not prove real model quality.
- No cloud GPU backend exists yet.
