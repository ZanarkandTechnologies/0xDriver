# TASK-001: Implement Fixture-Backed 0xDriver Pipeline

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: docs/prd.md, docs/specs/directory-structure-plan.md
- location: src/driverx, tests, configs, docs
- enter when: user approved implementation of the first version
- leave when: mock pipeline, CLIs, tests, evidence artifacts, docs, review, and QA pass
- blockers: none for fixture-backed v1
- spawned follow-ups: none yet
- complexity: L

## Description

Implement the first complete offline 0xDriver loop without requiring real Waymo
data or a VLA model. The system should run on synthetic fixture data, produce
visible artifacts and metrics, and leave optional seams for real Waymo data and
future cloud VLA inference.

## Goal

Turn the PRD into a runnable codebase that proves the architecture end to end:
frame input -> scene rendering -> structured intent -> candidate trajectories ->
smoothing/ranking -> ADE/latency/evidence -> dry-run submission package.

## Plan

### Change

Add a Python package with typed data models, fixture dataset generation,
reasoning/planning/evaluation/submission modules, and CLI entrypoints.

### Why

The project needs a working first version before real data/model integration.
Fixture-backed execution lets QA verify every user story except real Waymo
download access, while preserving the same interfaces real data will use.

### Before -> After

- Before: docs-only scaffold and planned module shape.
- After: installable package with `driverx` CLI commands, reproducible artifact
  output, tests, and final QA report.

### Touch

- `pyproject.toml`
- `src/driverx/**`
- `configs/*.yaml`
- `tests/**`
- `docs/progress.md`
- `PROJECT_RULES.md`
- `README.md`
- `qa/cookbook/*.md`

### Signature Delta

- `driverx.core.types / FrameBundle`: canonical frame object.
- `driverx.reasoning.base / Reasoner.infer_intent(frame)`: structured intent seam.
- `driverx.planning.candidates / generate_candidates(frame, intent)`: trajectory proposals.
- `driverx.planning.smoothing / smooth_trajectory(candidate)`: continuity constraints.
- `driverx.planning.ranking / rank_candidates(...)`: chosen prediction and rationale.
- `driverx.evaluation.ade / average_displacement_error(prediction, truth)`: local metric.
- `driverx.pipeline.scene_run / run_scene(config)`: one-scene orchestration.

### Type Sketch

```python
FrameBundle(frame_name, front_images, ego_history_xy, future_xy, metadata)
DrivingIntent(scene_type, hazards, ego_intent, target_behavior, speed_profile, lateral_bias, uncertainty)
TrajectoryCandidate(points_xy, source, score, metadata)
SceneRunResult(frame_name, intent, selected_trajectory, metrics, artifacts, timings)
```

### Typed Flow Example

`fixture:construction_merge_001` loads as `FrameBundle`, mock reasoning emits
`target_behavior="yield_then_proceed"`, planner creates brake/creep/bias-left
candidates, smoothing clamps jumps, ranking chooses the lowest cost candidate,
ADE compares it to fixture future labels, and artifacts are written under
`artifacts/runs/<run_id>/`.

### Execution Steps

1. Create package skeleton, pyproject, and CLI shell.
2. Add core types/config/artifact/timing utilities.
3. Add fixture dataset loader and optional Waymo loader placeholder.
4. Add visualization functions for camera strips and trajectory overlays.
5. Add reasoner schema, mock backend, and backend factory.
6. Add trajectory generation, smoothing, safety, and ranking.
7. Add ADE, latency reports, and submission dry-run packager.
8. Add pipeline orchestration and CLI commands.
9. Add tests and docs updates.
10. Run review and QA against PRD stories.

## Acceptance Criteria

- [x] `driverx inspect-scene --config configs/mock.yaml` writes a camera/trajectory artifact.
- [x] `driverx run-scene --config configs/mock.yaml` writes intent, trajectory, metric, latency, and overlay artifacts.
- [x] `driverx evaluate --run-dir <dir>` prints or writes ADE metrics.
- [x] `driverx package-submission --run-dir <dir>` creates a dry-run JSON/protobuf-compatible package artifact.
- [x] Tests cover schema validation, trajectory shape, smoothing, ADE, and mock pipeline execution.
- [x] Docs explain that real Waymo data is optional and configurable.
- [x] QA report maps evidence to PRD user stories.

## Evidence Checklist

- [x] Test run output.
- [x] Inspect-scene artifact.
- [x] Run-scene artifact directory.
- [x] Metrics and latency report.
- [x] Submission dry-run package.
- [x] Review result.
- [x] QA report.

## Build Notes

Implemented in modular commits:

- `5f98c57 feat(core): add driverx package skeleton`
- `8603fab feat(pipeline): add fixture autonomy loop`
- `079d427 test(pipeline): add mock verification gate`
- `e71bb28 feat(pipeline): add fixture batch runner`
- `53ccd19 docs(modules): document runtime ownership`
- `4a2cf1d feat(cli): add stable run output overrides`
- `9293fc9 fix(pipeline): strengthen evidence artifacts`

## QA Reconciliation

- US-001: PASS
- US-002: PASS
- US-003: PASS
- US-004: PASS for v1 package scope

## Artifact Links

- QA report: `qa/reports/TASK-001-final-qa.md`
- Review result: `docs/reviews/TASK-001-implementation-review.md`
- Inspect artifact: `artifacts/runs/final-qa2-inspect/scene_inspection.svg`
- Prediction artifact: `artifacts/runs/final-qa2-scene/scene_prediction.svg`
- Intent: `artifacts/runs/final-qa2-scene/intent.json`
- Raw candidates: `artifacts/runs/final-qa2-scene/raw_candidates.json`
- Smoothed candidates: `artifacts/runs/final-qa2-scene/smoothed_candidates.json`
- Metrics: `artifacts/runs/final-qa2-scene/metrics.json`
- Timings: `artifacts/runs/final-qa2-scene/timings.json`
- Submission protobuf shard: `artifacts/runs/final-qa2-scene/submission_shard_00000.pb`
- Invalid reasoner fallback: `artifacts/runs/final-qa2-invalid/reasoner_error.json`
- Batch summary: `artifacts/runs/final-qa2-batch/batch_summary.json`

## User Evidence

- Hero screenshot: `artifacts/runs/final-qa2-scene/scene_prediction.svg`
- Supporting evidence: `artifacts/runs/final-qa2-inspect/scene_inspection.svg`
- QA report: `qa/reports/TASK-001-final-qa.md`
- Final verdict: PASS for fixture-backed v1.
