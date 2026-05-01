# Core AGENTS.md

- Keep this module dependency-light and provider-neutral.
- Do not import dataset, model, planning, or visualization modules here.
- Preserve explicit data shapes; downstream modules rely on these boundaries.
