# TASK-035: Live OOD Overlay Injection Evidence

## Status

- state: done
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

- [x] Overlay run evidence links back to route pack recipe ids.
- [x] Behavior assertions validate cut-in/brake/filtering traces.
- [x] Report includes actor tracks and cleanup state.
- [x] Missing live CARLA returns a clean blocker.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_carla_injection tests.test_route_evidence`
- live optional: `scripts/run_carla_client_docker.sh python -m driverx run-overlay-injection ...`

## Blockers

- Live proof requires a reachable CARLA server.

## Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_overlay_evidence tests.test_carla_injection tests.test_route_evidence`
  passed with 10 tests.
- Local dry-run chain generated scenario, route pack, overlay plan, and
  `artifacts/runs/task35-overlay-evidence/overlay_evidence.json` plus
  `artifacts/runs/task35-overlay-evidence/overlay_evidence.md`. The evidence
  links back to recipe
  `generated-base-animals-0076-lane-blockage-000`, passes the
  `no_signal_cut_in` behavior assertion, and records the missing live overlay
  run path as a clean blocker.
- `bash scripts/pre_push_check.sh` passed with 179 tests.
- Review pass:
  `tickets/TASK-035/artifacts/review/20260505T190921-review.json` scored
  `4.0` overall with no blocking findings.
