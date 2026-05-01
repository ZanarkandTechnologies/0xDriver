# QA AGENTS.md

Read `PROJECT_RULES.md` before running QA. Keep evidence reproducible and avoid
assuming real Waymo data is present on every machine.

## Current Rules

- Do not require cloud GPU access for baseline QA.
- Prefer mock reasoner smoke tests before real-model tests.
- Treat generated artifacts as local output unless a ticket defines a checked-in
  fixture.
- Record dataset path assumptions and missing-data behavior.
