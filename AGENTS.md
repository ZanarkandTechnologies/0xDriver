# AGENTS.md

Project operational contract for 0xDriver. Keep this file lightweight; put
stack-specific details and commands in `PROJECT_RULES.md`.

## Build & Run

- Current phase: docs-first bootstrap and PRD.
- Install: not configured yet.
- Dev: not configured yet.
- QA path: not configured yet.
- Before adding runtime commands, update `PROJECT_RULES.md` and `qa/`.

## Validation

- Bootstrap gate: `bash scripts/pre_push_check.sh`
- Tests: not configured until code scaffolding lands.
- Typecheck: not configured until code scaffolding lands.
- Lint: not configured until code scaffolding lands.
- Build: not applicable yet.

## Docs State

- Architecture: `ARCHITECTURE.md`
- PRD: `docs/prd.md`
- Bootstrap: `docs/bootstrap-brief.md`
- Specs index: `docs/specs/README.md`
- History: `docs/HISTORY.md`
- Memory: `docs/MEMORY.md`
- Troubles: `docs/TROUBLES.md`
- Taste: `docs/TASTE.md`
- Tickets: active `tickets/TASK-*/ticket.md`, completed `tickets/archive/TASK-*/ticket.md`

## Context First

- Read `docs/prd.md`, `ARCHITECTURE.md`, and relevant specs before code edits.
- Search for existing patterns before adding modules.
- Keep Waymo dataset files, model weights, generated videos, and submission
  archives out of git unless a ticket explicitly changes artifact policy.
- No blind edits.

## Operating Modes

- Discovery mode: clarify product/research scope before PRD/spec changes.
- Planning mode: create or refresh durable specs/tickets before implementation.
- Build mode: execute approved tickets, then test and review.

## Project Bias

- Start with the smallest complete Waymo E2E offline pipeline.
- Treat VLA/VLM output as structured intent, not direct control.
- Prefer deterministic planners, smoothing, and safety checks around model output.
- Keep cloud GPU acceleration optional and swappable.

## Delegation Guardrails

- Use review before completion claims after meaningful docs or build passes.
- Use visual QA only when UI/demo surfaces change.
- Use runtime debugging for reproducible runtime/model/dataset failures once
  implementation begins.

## Notes

- Update the active ticket once tickets exist; do not keep task state only in chat.
- If repeated mistakes or operator corrections happen, append them to
  `docs/TROUBLES.md` before promoting durable lessons.
