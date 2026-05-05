# TASK-032: Board Normalize For Closed-Loop Video Phase

## Status

- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: TASK-031
- location: `tickets/`, `docs/progress.md`, `docs/HISTORY.md`
- enter when: setup-era tickets obscure the next closed-loop video work
- leave when: completed setup tickets are archived and TASK-033 through TASK-040
  define the next executable phase
- blockers: none
- spawned follow-ups: TASK-033, TASK-034, TASK-035, TASK-036, TASK-037,
  TASK-038, TASK-039, TASK-040
- complexity: S

## Summary

Normalize the board around the next submission-critical phase: Fail2Drive/CARLA
closed-loop video evidence first, policy adapters second. This ticket archives
completed or blocker-captured setup work and creates the next visible ticket
ladder.

## Scope

In scope:

- Move TASK-008 through TASK-031 to `tickets/archive/` because their evidence is
  complete or their external blocker is captured.
- Keep `blockers.md` as the live external blocker ledger.
- Create TASK-033 through TASK-040 as the next phase.
- Refresh `tickets/README.md`, `docs/progress.md`, and `docs/HISTORY.md`.

Out of scope:

- Delete source code or artifacts.
- Claim live Fail2Drive/CARLA video success.
- Rent, stop, or mutate cloud instances.

## Acceptance Criteria

- [x] Completed setup tickets live under `tickets/archive/`.
- [x] Active tickets describe the new closed-loop video phase.
- [x] H100/CARLA graphics blocker remains visible in `blockers.md`.
- [x] Progress and history point to route-video-first execution.

## Verification

- `find tickets -maxdepth 2 -name ticket.md | sort`
- `git status --short`

## Evidence

- TASK-008 through TASK-031 moved to `tickets/archive/`.
- TASK-033 through TASK-040 added under `tickets/`.
- `tickets/README.md` now lists the active closed-loop video phase.

## Blockers

- None.
