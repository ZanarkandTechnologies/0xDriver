# TASK-004 QA Report

## Verdict

PASS. TASK-004 produces a configurable real Waymo batch baseline with per-frame
artifacts, aggregate ADE/latency evidence, and fixture compatibility preserved.

## Commands

- `PYTHONPATH=src python3 -m unittest discover -s tests`
  - PASS: 34 tests.
- `bash scripts/pre_push_check.sh`
  - PASS: compile/test gate passed with 34 unittest cases.
- `scripts/run_waymo_docker.sh python -m driverx run-batch --config configs/waymo_local.sample.yaml --run-id waymo-batch-10 --frame-count 10`
  - PASS: streamed 10 real validation frames in the Linux amd64 Waymo runtime.
- `scripts/run_waymo_docker.sh python -m driverx run-batch --config configs/waymo_local.sample.yaml --run-id waymo-batch-default-10 --frame-start 0`
  - PASS: omitted `--frame-count` and still streamed the default 10 real
    validation frames.

## Acceptance Criteria Reconciliation

- Fixture `run-batch` compatibility: PASS. Existing fixture batch test passes
  and CLI fixture smoke wrote `artifacts/runs/task004-fixture-smoke`.
- Waymo `frame_start` / `frame_count`: PASS. CLI test covers both flags; fake
  Waymo batch test covers `frame_start=3`, `frame_count=2`; Docker proof covers
  `frame_start=0`, `frame_count=10`.
- Default Waymo count: PASS. Unit test omits `frame_count` and verifies
  `DEFAULT_WAYMO_BATCH_COUNT`; Docker proof omits `--frame-count` and writes
  `artifacts/runs/waymo-batch-default-10`.
- Real Waymo output artifacts: PASS. `artifacts/runs/waymo-batch-10` contains
  per-frame run dirs, `batch_summary.json`, and `batch_report.md`.
- Report contents: PASS. `batch_report.md` includes summary, ADE table, latency
  table, best/worst scenes, and worst-scene SVG path.
- No generated artifacts committed: PASS. Batch outputs remain under ignored
  `artifacts/runs/`; data remains under ignored `data/`.

## Real Batch Evidence

- Summary: `artifacts/runs/waymo-batch-default-10/batch_summary.json`
- Report: `artifacts/runs/waymo-batch-default-10/batch_report.md`
- Worst scene SVG: `artifacts/runs/waymo-batch-default-10/frame-000006/scene_prediction.svg`
- Mean ADE: `6.204769`
- Best scene: frame index `4`, ADE `0.517203`
- Worst scene: frame index `6`, ADE `13.953167`
- Mean timings include `load_frame`, `reason`, `generate_candidates`,
  `smooth_candidates`, `rank_candidates`, `evaluate`, `render_scene`, and
  `package_submission`.

## Residual Risk

This is intentionally still a mock-reasoner baseline. It proves the data,
planner, aggregation, and evidence paths; it does not claim VLA quality or
cloud-GPU latency.
