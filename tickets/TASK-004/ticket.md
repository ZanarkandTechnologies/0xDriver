# TASK-004: Real Waymo Batch Baseline And Report

## Status

- state: building
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

- [ ] Fixture `run-batch` behavior remains compatible with existing tests and CLI defaults.
- [ ] Waymo `run-batch` supports configurable `frame_start` and `frame_count`.
- [ ] Waymo batch defaults to 10 frames when no count is supplied.
- [ ] Real Waymo batch output includes per-frame run dirs, `batch_summary.json`, and `batch_report.md`.
- [ ] Report includes ADE table, latency table, best/worst scene, and a path to the worst-scene SVG.
- [ ] No dataset shards, generated artifacts, or credentials are committed.

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

- [ ] Snapshot: local unit/pre-push output
- [ ] Snapshot: Docker real-data batch command output
- [ ] Snapshot: `batch_summary.json`
- [ ] Snapshot: `batch_report.md`
- [ ] Snapshot: worst-scene `scene_prediction.svg` path
- [ ] QA report linked:

### Build Notes

- Implementation started 2026-05-02 20:42 +0800.
- Keep `mock` as the reasoner backend; no GPU or VLA service is introduced in this ticket.

### QA Reconciliation

- Fixture compatibility: PENDING
- Waymo frame range: PENDING
- Batch summary/report: PENDING
- Real-data Docker proof: PENDING
- Review: PENDING

### Artifact Links

### User Evidence

- Final verdict:
- Supporting evidence:
- QA report:

### Required Evidence

- [ ] Unit/integration/e2e tests pass as applicable.
- [ ] Docker real-data batch proof captured.
- [ ] Final review attached.
