# TASK-004: Real Waymo Batch Baseline And Report

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-003, local validation shard in `data/`
- location: `src/driverx/datasets`, `src/driverx/pipeline`, CLI, tests, docs
- enter when: TASK-003 proves one real Waymo frame can run in Docker
- leave when: a small real Waymo validation slice streams through `run-batch` and writes aggregate baseline evidence
- blockers: none
- spawned follow-ups: aggregate official Waymo submission packaging can be TASK-005 after the baseline is trustworthy
- complexity: M

## Description

Build the first real-data measuring stick by running the existing mock-reasoner
pipeline over a small Waymo validation slice, aggregating ADE and latency, and
writing a human-readable batch report. This ticket stays model-light: the point
is to establish evidence and failure cases before introducing VLA/GPU serving.

## Goal

Extend `run-batch` from fixture-only to fixture-or-Waymo execution with a
streaming Waymo frame path, per-frame artifacts, and batch-level summary/report
outputs.

## Plan

### Change

Add `iter_waymo_frames`, extract `run_loaded_scene`, and teach `run_batch` plus
the CLI to run either fixtures or a configurable Waymo frame range.

### Why

Repeatedly calling `run_scene` with increasing `frame_index` rereads the
TFRecord from the start for every scene. Streaming the batch once gives a more
honest baseline for local Docker and later cloud GPU experiments.

### Before -> After

- Before: `run-batch` only loops over named fixtures.
- After: `run-batch --config configs/waymo_local.sample.yaml --frame-count 10`
  streams 10 real frames and writes `batch_summary.json` plus `batch_report.md`.

### Touch

- `src/driverx/datasets/waymo_e2e.py`
- `src/driverx/pipeline/scene_run.py`
- `src/driverx/pipeline/batch_run.py`
- `src/driverx/cli.py`
- tests, README, progress, history, review evidence

### Acceptance Criteria

- [x] Fixture `run-batch` behavior remains compatible with existing tests and CLI defaults.
- [x] Waymo `run-batch` supports configurable `frame_start` and `frame_count`.
- [x] Waymo batch defaults to 10 frames when no count is supplied.
- [x] Real Waymo batch output includes per-frame run dirs, `batch_summary.json`, and `batch_report.md`.
- [x] Report includes ADE table, latency table, best/worst scene, and a path to the worst-scene SVG.
- [x] No dataset shards, generated artifacts, or credentials are committed.

### Agent Contract

- Open: `PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml`
- Test hook: `bash scripts/pre_push_check.sh`
- Stabilize: keep fixture path TensorFlow-free and Waymo deps lazily imported
- Inspect: `batch_summary.json`, `batch_report.md`, per-frame `scene_prediction.svg`
- Key screens/states: none
- QA cookbook: `qa/cookbook/mock-pipeline.md`, TASK-004 Docker command
- Taste refs: none
- Expected artifacts: `docs/reviews/TASK-004-batch-baseline-review.md`, batch summary/report paths
- Delegate with: reviewer/QA lanes may inspect diffs and evidence after implementation

### Evidence Checklist

- [x] Snapshot: local unit/pre-push output
- [x] Snapshot: Docker real-data batch command output
- [x] Snapshot: `batch_summary.json`
- [x] Snapshot: `batch_report.md`
- [x] Snapshot: worst-scene `scene_prediction.svg` path
- [x] QA report linked: `tickets/TASK-004/artifacts/qa/2026-05-02T125206Z/report.md`

### Build Notes

- Implementation started 2026-05-02 20:42 +0800.
- Keep `mock` as the reasoner backend; no GPU or VLA service is introduced in this ticket.
- Commit `f75405d` added `iter_waymo_frames`, `run_loaded_scene`, Waymo
  `run-batch` frame ranges, batch summaries/reports, and fake-Waymo tests.
- Local proof: `bash scripts/pre_push_check.sh` passed with 34 unittest cases.
- Docker proof: `scripts/run_waymo_docker.sh python -m driverx run-batch
  --config configs/waymo_local.sample.yaml --run-id waymo-batch-10
  --frame-count 10` completed successfully.
- Default-count Docker proof: `scripts/run_waymo_docker.sh python -m driverx
  run-batch --config configs/waymo_local.sample.yaml --run-id
  waymo-batch-default-10 --frame-start 0` completed successfully without
  `--frame-count`.
- Real batch result: mean ADE `6.204769`; best scene frame index `4` ADE
  `0.517203`; worst scene frame index `6` ADE `13.953167`.
- Review revision: fixture defaults are now centralized in `run_batch`, the CLI
  passes through `None`, and tests prove API/CLI agreement plus Waymo default
  count behavior.

### QA Reconciliation

- Fixture compatibility: PASS
- Waymo frame range: PASS
- Batch summary/report: PASS
- Real-data Docker proof: PASS
- Review: PASS, final score `4.4 / 5.0`
- QA report: PASS

### Artifact Links

- `artifacts/runs/waymo-batch-10/batch_summary.json`
- `artifacts/runs/waymo-batch-10/batch_report.md`
- `artifacts/runs/waymo-batch-10/frame-000006/scene_prediction.svg`
- `artifacts/runs/waymo-batch-default-10/batch_summary.json`
- `artifacts/runs/waymo-batch-default-10/batch_report.md`
- `artifacts/runs/waymo-batch-default-10/frame-000006/scene_prediction.svg`
- `tickets/TASK-004/artifacts/qa/2026-05-02T125206Z/report.md`
- `docs/reviews/TASK-004-batch-baseline-review.md`

### User Evidence

- Final verdict: PASS for real Waymo batch baseline and report.
- Supporting evidence: `waymo-batch-10` real-data Docker run produced 10
  per-frame run dirs; `waymo-batch-default-10` proved the default 10-frame path
  without `--frame-count`; both produced aggregate ADE/timing tables and
  worst-scene SVGs.
- QA report: `tickets/TASK-004/artifacts/qa/2026-05-02T125206Z/report.md`
- Review result: `docs/reviews/TASK-004-batch-baseline-review.md`

### Required Evidence

- [x] Unit/integration/e2e tests pass as applicable.
- [x] Docker real-data batch proof captured.
- [x] QA report attached.
- [x] Final review attached.
