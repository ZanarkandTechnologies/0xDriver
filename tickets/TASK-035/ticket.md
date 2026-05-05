# TASK-035: Live OOD Overlay Injection Evidence

## Status

- state: building
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-022, TASK-034
- location: `src/driverx/simulators`, CLI, tests, docs
- enter when: route/video evidence format exists and overlay runner can spawn
  companion actors
- leave when: an overlay injection run can be attached to route evidence with
  actor tracks and expected behavior assertions
- blockers: live proof needs CARLA Python API and a running simulator
- spawned follow-ups: TASK-036 generated OOD suite runner
- complexity: M

## Summary

Turn companion actor injection from a standalone proof into submission evidence:
which actor appeared, what behavior it executed, where it moved, and what
failure pressure it created.

## Acceptance Criteria

- [ ] Overlay run evidence links back to route pack recipe ids.
- [ ] Behavior assertions validate cut-in/brake/filtering traces.
- [ ] Report includes actor tracks and cleanup state.
- [ ] Missing live CARLA returns a clean blocker.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_route_evidence`
- live optional: `scripts/run_carla_client_docker.sh python -m driverx run-overlay-injection ...`

## Blockers

- Live proof requires a reachable CARLA server.
