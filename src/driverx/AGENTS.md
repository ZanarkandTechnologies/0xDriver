# driverx AGENTS.md

- Keep CLI code thin; orchestration belongs in `pipeline/`.
- Keep model/provider-specific logic inside `reasoning/`.
- Keep Waymo-specific parsing/serialization inside `datasets/` and `submission/`.
- Keep generated artifacts under `artifacts/`, not in this package.
