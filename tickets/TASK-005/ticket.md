# TASK-005: Batch Experiment Harness And Strong Baseline Planner

## Status

- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-004
- location: `src/driverx/planning`, `src/driverx/pipeline`, CLI, tests, docs
- enter when: TASK-004 establishes a real 10-frame Waymo batch baseline
- leave when: the same batch can compare multiple deterministic strategies and
  produce a cross-strategy experiment report
- blockers: none
- spawned follow-ups: VLA/cloud reasoner adapter should follow after this
  comparison harness exists
- complexity: M

## Summary

Build the next measuring stick after TASK-004: compare the current
intent-planner against simple deterministic trajectory baselines over the same
fixture or Waymo batch, then write an experiment summary/report that shows which
baseline the VLA path must beat.

## Scope

In scope:

- deterministic rule baselines from ego history
- a new batch experiment pipeline and CLI command
- per-frame strategy artifacts and aggregate comparison reports
- fixture and fake-Waymo tests that do not require TensorFlow
- one real 10-frame Waymo Docker proof

Out of scope:

- cloud GPU or VLA backend integration
- official aggregate Waymo submission packaging
- training or tuning model weights

## Plan

### Change

Add a `run-experiment` path that streams the same frames once, evaluates:

- `intent_planner`: existing mock-reasoner planner
- `constant_velocity`: last-step ego velocity extrapolation
- `constant_acceleration`: two-step ego acceleration extrapolation
- `cautious_stop`: velocity decay to a stop
- `rule_ranked`: deterministic ranker choice among rule baselines
- `oracle_best_rule`: analysis-only upper bound among rule baselines when ground
  truth exists

### Why

TASK-004 proved the data/evidence loop, but it only measured the current
mock-intent planner. Before adding a VLA backend, we need a stricter baseline
table so semantic reasoning has a concrete target rather than a vibes-based
success story.

### Before -> After

- Before: one method produces one batch ADE/report.
- After: one experiment compares several strategies on the same streamed frames
  and names the best/worst strategy, best/worst scenes, and the current
  intent-planner delta.

### Touch

- `src/driverx/planning/baselines.py`: deterministic history-based trajectory
  strategies.
- `src/driverx/planning/__init__.py`, `src/driverx/planning/README.md`: public
  API and local docs.
- `src/driverx/pipeline/experiment_run.py`: experiment orchestration and report
  writing.
- `src/driverx/pipeline/__init__.py`, `src/driverx/pipeline/README.md`: expose
  the experiment seam.
- `src/driverx/cli.py`: add `run-experiment`.
- `tests/test_trajectory.py`, `tests/test_experiment.py`, `tests/test_cli.py`:
  strategy shape, fake-Waymo aggregation, CLI flags.
- `README.md`, `docs/progress.md`, `docs/HISTORY.md`, `docs/MEMORY.md`,
  `tickets/TASK-005/ticket.md`: usage and durable evidence.

### Inspect

- `src/driverx/planning/candidates.py`
- `src/driverx/planning/smoothing.py`
- `src/driverx/planning/ranking.py`
- `src/driverx/pipeline/batch_run.py`
- `src/driverx/pipeline/scene_run.py`
- `src/driverx/evaluation/ade.py`
- `src/driverx/core/types.py`
- `docs/prd.md`
- `docs/specs/directory-structure-plan.md`
- `docs/MEMORY.md`
- `docs/TROUBLES.md`

### Signature Delta

```python
# planning
generate_rule_baselines(frame: FrameBundle) -> list[TrajectoryCandidate]

# pipeline
run_experiment(
    config: DriverConfig,
    frame_start: int | None = None,
    frame_count: int | None = None,
) -> dict[str, Any]

# CLI
python -m driverx run-experiment \
  --config configs/waymo_local.sample.yaml \
  --run-id waymo-experiment-10 \
  --frame-start 0 \
  --frame-count 10
```

### Type Sketch

```python
StrategyFrameResult = {
  "strategy": str,
  "source": str,
  "ade": float | None,
  "score": float,
  "trajectory_path": str,
}

ExperimentFrameRecord = {
  "frame_index": int | None,
  "frame_name": str,
  "run_dir": str,
  "strategies": dict[str, StrategyFrameResult],
}

StrategySummary = {
  "strategy": str,
  "mean_ade": float | None,
  "best_scene": StrategyFrameResult | None,
  "worst_scene": StrategyFrameResult | None,
}

ExperimentSummary = {
  "experiment_id": str,
  "dataset_kind": "fixture" | "waymo",
  "frame_start": int | None,
  "frame_count": int,
  "num_scenes": int,
  "strategy_summaries": dict[str, StrategySummary],
  "best_strategy_by_mean_ade": str | None,
  "frames": list[ExperimentFrameRecord],
  "summary_path": str,
  "report_path": str,
}
```

### Typed Flow Example

`configs/waymo_local.sample.yaml + frame_count=10`
-> `iter_waymo_frames(...)` streams `FrameBundle`s once
-> for frame `6`, `run_loaded_scene(...)` writes `intent_planner` artifacts
-> `generate_rule_baselines(frame)` creates three rule candidates
-> smoothing/ranking/evaluation write `rule_baselines.json`
-> `run_experiment(...)` aggregates per-strategy ADE
-> `experiment_report.md` shows whether `intent_planner` beats
`constant_velocity`, `constant_acceleration`, `cautious_stop`, and `rule_ranked`.

### Execution Steps

1. Create the TASK-005 ticket with this plan.
2. Add deterministic baseline trajectory functions in `planning/baselines.py`.
3. Add experiment orchestration that reuses `run_loaded_scene` for
   `intent_planner` and writes per-frame rule baseline artifacts.
4. Add aggregate strategy summaries and Markdown report generation.
5. Add `run-experiment` CLI flags matching `run-batch` frame controls.
6. Add unit tests for trajectory shape, fake-Waymo experiment aggregation, CLI
   parsing, and default 10-frame behavior.
7. Run local checks.
8. Run a Docker real-data 10-frame experiment.
9. Update README, progress, history, memory, ticket evidence, QA, and review.

### Recommendation

Use a separate `run-experiment` command rather than extending `run-batch`.
`run-batch` remains the single-method evidence runner; `run-experiment` becomes
the cross-method comparison surface.

### Options Considered

- Extend `run-batch` with strategy flags.
  - Pros: fewer commands.
  - Cons: mixes single-method evidence with cross-method analysis and makes the
    summary schema harder to trust.
- Recommended: add `run-experiment`.
  - Pros: clean ownership, clearer reports, safer future VLA comparisons.
  - Cons: one more CLI command to document.
- Jump straight to VLA/cloud backend.
  - Pros: more exciting demo path.
  - Cons: premature; no strong local comparator yet.

### Blast Radius

- CLI gains one command but existing commands stay compatible.
- Planning public API gains rule baselines.
- Pipeline public API gains `run_experiment`.
- Generated artifacts are under ignored `artifacts/`.
- No dataset shards, model weights, credentials, or cloud calls are introduced.

### Risks

- Rule baselines may outperform the current mock intent planner; that is a good
  failure because it tells us the VLA backend must add semantic value.
- `oracle_best_rule` must be clearly labeled analysis-only because it uses
  ground truth to choose the best rule candidate.
- Experiment reports must not overclaim hidden Waymo rater quality; ADE remains
  a local proxy.

## Gap Analysis

Current state:

- TASK-004 measures one selected trajectory per frame.
- The system can identify a worst scene, but cannot say whether that failure is
  caused by semantic intent, trajectory extrapolation, or a weak baseline.

Production-grade expectation for this stage:

- Every future VLA backend should be compared against simple non-VLA baselines
  on the same frames, with the same ADE metric, and with explicit failure cases.

Recommended now/later boundary:

- Now: deterministic baseline comparison and report.
- Later: VLA/cloud backend, prompt cache, and submission-packaging comparison.

## Acceptance Criteria

- [ ] `run-experiment` works on fixture configs without TensorFlow.
- [ ] `run-experiment` works on fake Waymo frames in unit tests without TensorFlow.
- [ ] `run-experiment` supports `--frame-start` and `--frame-count`.
- [ ] Waymo experiments default to 10 frames when no count is supplied.
- [ ] Experiment output includes per-frame strategy artifacts,
  `experiment_summary.json`, and `experiment_report.md`.
- [ ] Report includes strategy mean ADE table, per-frame ADE table, best/worst
  strategy, and labels `oracle_best_rule` as analysis-only.
- [ ] Real Docker run over the downloaded validation shard completes.
- [ ] No dataset shards, generated artifacts, or credentials are committed.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_trajectory tests.test_experiment tests.test_cli`
- `bash scripts/pre_push_check.sh`
- Docker proof:

```bash
scripts/run_waymo_docker.sh python -m driverx run-experiment \
  --config configs/waymo_local.sample.yaml \
  --run-id waymo-experiment-10 \
  --frame-start 0 \
  --frame-count 10
```

- Review artifact: `docs/reviews/TASK-005-experiment-review.md`.
- QA artifact: `tickets/TASK-005/artifacts/qa/<timestamp>/report.md`.

## Evidence

- Local test output:
- Docker command output:
- `artifacts/runs/waymo-experiment-10/experiment_summary.json`:
- `artifacts/runs/waymo-experiment-10/experiment_report.md`:
- Worst strategy/frame evidence:
- Review:
- QA:

## Blockers

None.
