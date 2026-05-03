# Planning AGENTS.md

- Do not read ground truth future labels for ranking.
- Keep Waymo protobuf and model-provider logic out of this module.
- All public trajectories must contain exactly 20 `(x, y)` points.
- MEM-0010: keep deterministic rule baselines in VLA/GPU comparison reports so
  semantic model changes beat simple ego-history extrapolation, not just the
  mock intent planner.
- MEM-0011: keep the main planner hybrid by default; future VLA/GPU backends
  should steer or beat the local semantic-plus-motion-prior action layer, not
  bypass it with direct model-only control.
