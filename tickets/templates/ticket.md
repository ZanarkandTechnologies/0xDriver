# Ticket Template

Use this template to create ticket files directly under `tickets/`.

## Ticket Lifecycle

`todo -> review -> building -> done`

- Start with `status: todo`.
- Set `status: review` while planning and human approval are happening.
- Set `status: building` only after approval.
- Set `status: done` only after implementation, QA, and final human confirmation.

## Template

```markdown
# TKT-001: [Clear Action Title]

## Status
- state: todo | review | building | done
- owner:
- assignee:
- dependencies:
- location:
- enter when:
- leave when:
- blockers:
- spawned follow-ups:
- dependencies:
- complexity: S | M | L
- assignee: convex-builder | frontend-designer | qa-tester | generalPurpose

### Description
[2-4 sentences]

### Goal
[1-2 sentences: what this ticket includes and why]

### Acceptance Criteria
- [ ] AC-1: [Specific, testable outcome]
- [ ] AC-2: [Specific, testable outcome]

### Agent Contract
- Open:
- Test hook:
- Stabilize:
- Inspect:
- Key screens/states:
- QA cookbook:
- Taste refs:
- Expected artifacts:
- Delegate with:

### Evidence Checklist
- [ ] Screenshot:
- [ ] Screenshot:
- [ ] Snapshot:
- [ ] QA report linked:

### Build Notes

### QA Reconciliation
- AC-1: PASS | FAIL | NOT PROVABLE
- Screen: PASS | FAIL | NOT PROVABLE
- Evidence item: CAPTURED | MISSING

### Artifact Links

### User Evidence
- Hero screenshot:
- Supporting evidence:
- QA report:
- Final verdict:

### Required Evidence
- [ ] Unit/integration/e2e tests pass (as applicable)
- [ ] Typecheck passes
- [ ] Lint passes
```

## Dependency Graph (Optional)

```text
TASK-001 (schema)
    ->
TASK-002 (backend)
    ->
TASK-003 (ui)
```

## Complexity Rubric

- S: 1-2 hours
- M: half day
- L: full day

If larger than L, split the ticket.

## Planning Checklist

- Each ticket file is independently implementable.
- Dependencies are explicit (no cycles).
- Acceptance criteria map to the spec.
- Assignee matches task type.
- Control fields define when the ticket should move and what is blocking it.
- UI-bearing tickets define how agents open, inspect, verify, and delegate from the ticket artifact.
- UI-bearing tickets include a short evidence checklist for screenshots/snapshots/report proof.
- User Evidence gives one compact handoff packet for human review.
