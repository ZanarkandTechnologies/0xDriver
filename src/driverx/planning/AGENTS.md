# Planning AGENTS.md

- Do not read ground truth future labels for ranking.
- Keep Waymo protobuf and model-provider logic out of this module.
- All public trajectories must contain exactly 20 `(x, y)` points.
