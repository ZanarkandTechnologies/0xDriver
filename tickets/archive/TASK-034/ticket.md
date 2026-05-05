# TASK-034: Video And Telemetry Evidence Pipeline

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-033
- location: `src/driverx/pipeline`, `src/driverx/simulators`, CLI, tests
- enter when: route smoke plans can name result/RGB/video artifacts
- leave when: one report normalizes video, result JSON, entity tracks,
  infractions, latency, and screenshots into a demo-ready evidence bundle
- blockers: real videos require a live route run; fixture evidence is unblocked
- spawned follow-ups: TASK-035 live OOD overlay injection
- complexity: M

## Summary

Create the artifact collector that makes live or mocked route runs reviewable.
The collector should treat a missing video as a blocker, not a crash, and still
produce a report that says what evidence is ready.

## Acceptance Criteria

- [x] Load optional route result JSON, entity tracks, video path, screenshots,
  and logs.
- [x] Write `run_evidence.json` and `run_evidence.md`.
- [x] Surface missing video/result/track artifacts as blockers.
- [x] Include video duration/path when present.
- [x] Tests use tiny fixture files and no CARLA/GPU.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_route_evidence`
- `bash scripts/pre_push_check.sh`

## Blockers

- Real route videos depend on TASK-033 live proof.

## Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_route_evidence` passed with 3
  tests.
- `PYTHONPATH=src python3 -m driverx build-route-evidence --plan artifacts/runs/task33-video-smoke-review/fail2drive_video_smoke_plan.json --output-root artifacts/runs --run-id task34-from-task33-plan`
  wrote `artifacts/runs/task34-from-task33-plan/run_evidence.json` and
  `artifacts/runs/task34-from-task33-plan/run_evidence.md`, with missing live
  result/video and inherited TASK-033 blockers surfaced cleanly.
- `bash scripts/pre_push_check.sh` passed with 176 tests.
- Review pass:
  `tickets/TASK-034/artifacts/review/20260505T190442-review.json` scored
  `4.0` overall with no blocking findings.
