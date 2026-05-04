# TASK-009: Ego Spawn, Camera Capture, And Entity Tracks

## Status

- state: review
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-008
- location: `src/driverx/simulators`, `src/driverx/entities`, CLI, scripts, tests
- enter when: CARLA API probe works or degrades with a known runtime blocker
- leave when: one ego actor, one RGB sensor, one frame, and entity tracks are captured with cleanup
- blockers: live CARLA API bridge preferred for final proof; offline mocks can be implemented without it
- spawned follow-ups: TASK-010 behavior scripts, TASK-011 script compiler
- complexity: M

## Summary

Prove 0xDriver can create and observe CARLA entities, then clean them up. This
is the bridge from simulator introspection to generated scenario execution.

## Scope

In scope:

- ego vehicle spawn plan and cleanup.
- RGB camera sensor attachment.
- one-frame capture artifact.
- per-tick actor transform logging.
- local tests using fake CARLA objects.

Out of scope:

- full Fail2Drive route following.
- VLA policy control.

## Acceptance Criteria

- [ ] Spawn command can run in dry-run/fake mode without CARLA.
- [ ] Live command can spawn/destroy actors when CARLA bridge is available.
- [ ] Entity tracks include actor id, type, timestamp, transform, velocity when available.
- [ ] Sensor capture writes image metadata and a frame artifact.
- [ ] Cleanup runs in `finally` and logs destroyed actor ids.
- [ ] Tests prove cleanup on success and failure.

## Verification

- `bash scripts/pre_push_check.sh`
- live Docker proof after TASK-008:
  `bash scripts/run_carla_client_docker.sh python -m driverx spawn-ego-smoke --host host.docker.internal --port 2000 --run-id task9-ego-smoke`

## Blockers

- Requires TASK-008 for live proof; implementation can start with fakes.
