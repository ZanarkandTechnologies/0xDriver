# TASK-034: Video And Telemetry Evidence Pipeline

## Status

- state: building
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

- [ ] Load optional route result JSON, entity tracks, video path, screenshots,
  and logs.
- [ ] Write `run_evidence.json` and `run_evidence.md`.
- [ ] Surface missing video/result/track artifacts as blockers.
- [ ] Include video duration/path when present.
- [ ] Tests use tiny fixture files and no CARLA/GPU.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_route_evidence`
- `bash scripts/pre_push_check.sh`

## Blockers

- Real route videos depend on TASK-033 live proof.
