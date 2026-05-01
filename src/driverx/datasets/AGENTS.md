# Datasets AGENTS.md

- Keep real Waymo dependencies optional until a ticket explicitly enables them.
- Do not let fixture behavior depend on network, cloud GPU, or external files.
- Return `FrameBundle` only; projection/rendering belongs in `vision/`.
