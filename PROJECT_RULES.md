# Project Rules: 0xDriver

This file defines project-specific technical rules, stack choices, validation
expectations, and runtime assumptions.

## Tech Stack

- Language: Python first for data/model/evaluation work; TypeScript only if a
  later web demo is added.
- Runtime: Python 3.11 or newer.
- Data: Waymo Open Dataset End-to-End Driving TFRecords and protobufs.
- ML/VLM integration: provider-neutral adapter layer; first implementation may
  use cloud GPU inference or API-backed VLM calls.
- Notebooks: Jupyter for exploration and final analysis.
- Visualization: matplotlib/OpenCV for dataset overlays; optional rerun/RRD or
  video export later.
- Package manager: stdlib-first Python package for v1; use editable install or
  `PYTHONPATH=src` during local development.

## Folder Structure

- `ARCHITECTURE.md`: top-level system map and canonical surface guide.
- `docs/`: canonical project state, PRD, specs, memory, history, taste, and troubles.
- `docs/specs/`: durable planning specs before tickets are created.
- `qa/`: reusable verification and evidence-capture guidance.
- `tickets/`: future ticket board and archived work.
- `scripts/`: repo-local validation helpers.
- `src/driverx/`: implementation surface.
- `notebooks/`: analysis notebook placeholders.
- `data/`: local ignored data mount instructions, not checked-in dataset files.

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
- Required local commands:
  - Lint/syntax: `python3 -m compileall -q src tests`
  - Typecheck: not configured yet.
  - Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`
  - Build: optional unless packaging/distribution is added.
- Optional heavy checks:
  - Desloppify: manual workflow only for v1.
  - CodeRabbit: manual workflow only for v1.

## Runtime / QA Commands

- Authoritative app-only run path:
  `PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml`
- Authoritative QA / evidence run path:
  `bash scripts/pre_push_check.sh`
- Required local services: none for docs; future cloud GPU is optional for VLA
  inference and not required for local dataset parsing.
- Launch shape: local Python processes and notebooks first; optional remote
  inference server later.
- Expected local targets / base URLs: none yet.
- Port / env contract:
  - Future service ports must be configurable.
  - Future dataset paths must be controlled by environment variables or config,
    not hardcoded absolute paths.
- Source of truth note: CLI commands run through `python3 -m driverx` until an
  editable install is required.

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
# Inspect one fixture scene
PYTHONPATH=src python3 -m driverx inspect-scene --config configs/mock.yaml

# Run the fixture pipeline
PYTHONPATH=src python3 -m driverx run-scene --config configs/mock.yaml

# Run the tiny fixture validation batch
PYTHONPATH=src python3 -m driverx run-batch --config configs/mock.yaml

# Run tests
PYTHONPATH=src python3 -m unittest discover -s tests

# Run the local pre-push gate
bash scripts/pre_push_check.sh
```
