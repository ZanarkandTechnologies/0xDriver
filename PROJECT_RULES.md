# Project Rules: 0xDriver

This file defines project-specific technical rules, stack choices, validation
expectations, and runtime assumptions.

## Tech Stack

- Language: Python first for data/model/evaluation work; TypeScript only if a
  later web demo is added.
- Runtime: Python 3.10 or 3.11.
- Data: Waymo Open Dataset End-to-End Driving TFRecords and protobufs.
- ML/VLM integration: provider-neutral adapter layer; first implementation may
  use cloud GPU inference or API-backed VLM calls.
- Notebooks: Jupyter for exploration and final analysis.
- Visualization: matplotlib/OpenCV for dataset overlays; optional rerun/RRD or
  video export later.
- Package manager: not chosen yet; prefer `uv` for Python if no blocker appears.

## Folder Structure

- `ARCHITECTURE.md`: top-level system map and canonical surface guide.
- `docs/`: canonical project state, PRD, specs, memory, history, taste, and troubles.
- `docs/specs/`: durable planning specs before tickets are created.
- `qa/`: reusable verification and evidence-capture guidance.
- `tickets/`: future ticket board and archived work.
- `scripts/`: repo-local validation helpers.
- Future `src/`: implementation surface, created only after planning.
- Future `notebooks/`: analysis notebooks, created when the first notebook ticket lands.
- Future `data/`: local ignored data mount instructions, not checked-in dataset files.

## Conventions

- Start docs-first for architecture and PRD work; do not write runtime code
  before the initial implementation plan is accepted.
- Keep model integrations behind narrow interfaces so cloud GPU, API-backed VLM,
  and mock backends can be swapped.
- Store large datasets, generated videos, submission archives, and model weights
  outside git unless a later ticket adds explicit artifact handling.
- Prefer deterministic trajectory generation and verification around stochastic
  model outputs.
- Public Python APIs should have typed signatures and explicit return types once
  implementation begins.

## Shared Utilities

- Preferred shared utility location: future `src/driverx/common/` for real
  multi-module reuse.
- Keep local when: helper logic belongs to one module, one notebook, or one
  experiment.
- Extract when: the same logic is needed by loader, evaluator, visualizer, and
  submission paths.

## Pre-Push Policy

- Warn on large tracked source files: 500 raw lines.
- Block on oversized tracked source files: 1000 raw lines.
- Required local commands for the current docs-only bootstrap:
  - Lint: not configured yet.
  - Typecheck: not configured yet.
  - Tests: not configured yet.
  - Build: not applicable yet.
- Required commands after Python scaffolding lands:
  - Lint: `uv run ruff check .` or equivalent.
  - Typecheck: `uv run pyright` or equivalent.
  - Tests: `uv run pytest`.
  - Build: optional unless packaging is added.
- Optional heavy checks:
  - Desloppify: manual workflow only for v1.
  - CodeRabbit: manual workflow only for v1.

## Runtime / QA Commands

- Authoritative app-only run path: not applicable until runtime scaffolding lands.
- Authoritative QA / evidence run path: not applicable until runtime scaffolding lands.
- Required local services: none for docs; future cloud GPU is optional for VLA
  inference and not required for local dataset parsing.
- Launch shape: local Python processes and notebooks first; optional remote
  inference server later.
- Expected local targets / base URLs: none yet.
- Port / env contract:
  - Future service ports must be configurable.
  - Future dataset paths must be controlled by environment variables or config,
    not hardcoded absolute paths.
- Source of truth note: update this file when package scripts, notebook launch
  commands, or server/client commands become real.

## Agent QA / Testability

- Reusable QA runbooks live in `qa/cookbook/`.
- Preferred proof surfaces:
  - validation ADE table over a small local sample
  - rendered camera panels with ground-truth and predicted trajectories
  - latency breakdown table by pipeline stage
  - packaged submission dry-run
- Important future probes:
  - raw VLA structured output
  - pre-smooth trajectory
  - post-smooth trajectory
  - scoring/ranking rationale

## Quick Commands

```bash
# Run the local pre-push gate
bash scripts/pre_push_check.sh
```
