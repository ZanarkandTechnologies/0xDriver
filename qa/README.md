# QA

QA guidance for 0xDriver lives here. The first implementation should make a
small, repeatable evidence path before scaling to large Waymo runs.

## Expected Proof Surfaces

- One-frame dataset/fixture smoke run.
- Rendered camera strip with trajectory overlay.
- Raw structured intent JSON.
- Pre-smooth and post-smooth trajectory artifacts.
- ADE and latency tables.
- Dry-run submission shard packaging.

## Current State

No runtime QA commands exist yet. Update `PROJECT_RULES.md` and this folder when
the Python package and notebooks are created.
