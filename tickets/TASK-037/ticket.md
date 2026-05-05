# TASK-037: Policy Runtime Matrix

## Status

- state: building
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

- [ ] Matrix rows include policy, runtime kind, required hardware, ready state,
  command/config path, and blocker.
- [ ] Expert/basic/mock policies can be marked ready without model downloads.
- [ ] SimLingo/Alpamayo blockers are precise and do not block other rows.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_policy_runtime_matrix`
- `bash scripts/pre_push_check.sh`

## Blockers

- None for local matrix generation.
