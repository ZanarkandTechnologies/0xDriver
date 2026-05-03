# TASK-006 QA Report

## Verdict

PASS. TASK-006 routes the main pipeline through a hybrid semantic-intent plus
motion-prior planner, preserves label-free ranking, and records fresh real
Waymo evidence for both batch and experiment surfaces.

## Commands

- `PYTHONPATH=src python3 -m unittest tests.test_trajectory tests.test_pipeline_mock tests.test_batch tests.test_experiment tests.test_cli`
  - PASS: 20 focused tests.
- `bash scripts/pre_push_check.sh`
  - PASS: compile/test gate passed with 40 unittest cases.
- `PYTHONPATH=src python3 -m driverx run-experiment --config configs/mock.yaml --run-id task-006-fixture-experiment`
  - PASS: fixture experiment wrote `hybrid_planner` strategy artifacts.
- `scripts/run_waymo_docker.sh python -m driverx run-batch --config configs/waymo_local.sample.yaml --run-id waymo-hybrid-batch-10 --frame-start 0 --frame-count 10`
  - PASS: streamed 10 real validation frames through the main hybrid batch path.
- `scripts/run_waymo_docker.sh python -m driverx run-experiment --config configs/waymo_local.sample.yaml --run-id waymo-hybrid-experiment-10 --frame-start 0 --frame-count 10`
  - PASS: streamed 10 real validation frames through the experiment path and
    wrote fresh `hybrid_planner` strategy evidence.

## Acceptance Criteria Reconciliation

- AC-1 main `run-scene`/`run-batch` uses hybrid candidates: PASS.
  `src/driverx/pipeline/scene_run.py` calls `generate_hybrid_candidates`.
- AC-2 hybrid candidates include semantic and motion-prior sources with 20
  points: PASS. `tests.test_trajectory` covers both candidate families.
- AC-3 ranking remains deployable and does not inspect `future_xy`: PASS.
  `rank_candidates` still ranks from candidate priors, obstacle cost,
  smoothness cost, speed penalty, and fallback penalty; ADE remains in
  evaluation/report code.
- AC-4 real 10-frame Waymo batch evidence captured: PASS.
  `waymo-hybrid-batch-10` includes `batch_summary.json`, `batch_report.md`, and
  worst-scene SVG.
- AC-5 existing behavior remains compatible: PASS. Pre-push check passed with
  fixture, batch, experiment, CLI, packaging, and optional dependency tests.
- AC-6 docs, history, memory, review, and QA evidence updated: PASS after this
  QA report and the linked review artifact.

## Real Batch Evidence

- Summary: `artifacts/runs/waymo-hybrid-batch-10/batch_summary.json`
- Report: `artifacts/runs/waymo-hybrid-batch-10/batch_report.md`
- Mean ADE: `3.73323`
- Selected source: `constant_acceleration_smooth` for all 10 frames
- Best scene: frame index `4`, ADE `0.012684`
- Worst scene: frame index `6`, ADE `9.15508`
- Worst-scene SVG:
  `artifacts/runs/waymo-hybrid-batch-10/frame-000006/scene_prediction.svg`

## Real Experiment Evidence

- Summary: `artifacts/runs/waymo-hybrid-experiment-10/experiment_summary.json`
- Report: `artifacts/runs/waymo-hybrid-experiment-10/experiment_report.md`
- Mean ADE:
  - `hybrid_planner`: `3.73323`
  - `constant_acceleration`: `3.73323`
  - `constant_velocity`: `3.835549`
  - `rule_ranked`: `3.73323`
  - `cautious_stop`: `5.642078`
  - `oracle_best_rule`: `3.732298` analysis-only

## Residual Risk

The first hybrid planner now mostly behaves like the constant-acceleration
motion prior on the first real Waymo slice. That is intentional for TASK-006:
the local action layer is credible, but the next VLA/GPU ticket must add
semantic value that beats this baseline instead of merely matching it.
