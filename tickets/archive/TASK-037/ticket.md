# TASK-037: Policy Runtime Matrix

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-036, TASK-013
- location: `src/driverx/policies`, `src/driverx/pipeline`, CLI, tests
- enter when: suite plans exist and policies need to be compared without making
  one model the project foundation
- leave when: one scenario/suite can be planned against expert/basic/mock,
  SimLingo, and Alpamayo adapters with clear runtime blockers
- blockers: live SimLingo/Alpamayo require model runtimes and GPU access
- spawned follow-ups: TASK-038 Alpamayo offline probe
- complexity: M

## Summary

Create a runtime matrix that tells us which policy adapters are ready for which
scenario evidence path, and why blocked adapters are blocked.

## Acceptance Criteria

- [x] Matrix rows include policy, runtime kind, required hardware, ready state,
  command/config path, and blocker.
- [x] Expert/basic/mock policies can be marked ready without model downloads.
- [x] SimLingo/Alpamayo blockers are precise and do not block other rows.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_policy_runtime_matrix`
- `bash scripts/pre_push_check.sh`

## Blockers

- None for local matrix generation.

## Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_policy_runtime_matrix` passed
  with 3 tests.
- `PYTHONPATH=src python3 -m driverx build-policy-runtime-matrix --carla-config configs/carla_local.sample.yaml --simlingo-config configs/simlingo.sample.yaml --suite artifacts/runs/task36-suite-1b/route-pack/bench2drive_routes/generated_routes.xml --run-id task37-policy-matrix-review`
  wrote `artifacts/runs/task37-policy-matrix-review/policy_runtime_matrix.json`
  and `.md`, with `5` ready/planned rows and precise SimLingo/Alpamayo
  blockers.
- `bash scripts/pre_push_check.sh` passed with 184 tests.
- Review pass:
  `tickets/TASK-037/artifacts/review/20260505T191837-review.json` scored
  `4.0` overall with no blocking findings.
