# TASK-005 QA Report

## Verdict

PASS. TASK-005 adds a cross-strategy experiment harness, deterministic
ego-history baselines, and real 10-frame Waymo comparison evidence.

## Commands

- `PYTHONPATH=src python3 -m unittest tests.test_trajectory tests.test_experiment tests.test_cli`
  - PASS: 11 tests.
- `bash scripts/pre_push_check.sh`
  - PASS: compile/test gate passed with 39 unittest cases.
- `PYTHONPATH=src python3 -m driverx run-experiment --config configs/mock.yaml --run-id task005-fixture-experiment`
  - PASS: fixture experiment wrote summary/report artifacts.
- `scripts/run_waymo_docker.sh python -m driverx run-experiment --config configs/waymo_local.sample.yaml --run-id waymo-experiment-10 --frame-start 0 --frame-count 10`
  - PASS: streamed 10 real validation frames and compared all strategies.

## Acceptance Criteria Reconciliation

- Fixture `run-experiment`: PASS.
- Fake Waymo experiment without TensorFlow: PASS.
- `--frame-start` / `--frame-count`: PASS.
- Waymo default 10-frame behavior: PASS via unit test.
- Experiment artifacts: PASS. `waymo-experiment-10` includes per-frame strategy
  trajectories, `experiment_summary.json`, and `experiment_report.md`.
- Strategy report contents: PASS. The report includes strategy mean ADE table,
  per-frame ADE table, best deployable strategy, best analysis-only strategy,
  and labels `oracle_best_rule` as analysis-only.
- Real Docker run: PASS.
- No generated artifacts committed: PASS. Run outputs remain under ignored
  `artifacts/runs/`; data remains under ignored `data/`.

## Real Experiment Evidence

- Summary: `artifacts/runs/waymo-experiment-10/experiment_summary.json`
- Report: `artifacts/runs/waymo-experiment-10/experiment_report.md`
- Best deployable strategy: `constant_acceleration`
- Best analysis-only strategy: `oracle_best_rule`
- Mean ADE:
  - `constant_acceleration`: `3.73323`
  - `constant_velocity`: `3.835549`
  - `rule_ranked`: `3.835549`
  - `cautious_stop`: `5.642078`
  - `intent_planner`: `6.204769`
  - `oracle_best_rule`: `3.732298`

## Residual Risk

The current mock intent planner is weaker than simple motion extrapolation on
this slice. That is an expected and useful result: future VLA work now has to
beat `constant_acceleration`, not just the previous mock planner baseline.
