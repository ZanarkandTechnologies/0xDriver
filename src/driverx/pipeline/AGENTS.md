# Pipeline AGENTS.md

- Orchestrate only; do not bury planner, reasoner, renderer, or evaluator logic here.
- Save intermediate artifacts needed for QA and failure analysis.
- Keep batch runs fixture-compatible and deterministic.
- MEM-0009: treat real Waymo `batch_summary.json` and `batch_report.md` as the baseline surface before adding or comparing VLA/GPU backends.
