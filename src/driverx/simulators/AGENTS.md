# AGENTS.md

Simulator adapter namespace.

- Keep local command planning dependency-light and dry-run friendly.
- Do not launch CARLA or Fail2Drive from tests.
- Fail2Drive plans must use an explicit route-backed recipe; do not silently
  fall back from a generated recipe to an unrelated config route. See
  `MEM-0014`.
- Treat Apple Silicon CARLA as optional smoke infrastructure; reproducible
  benchmark runs target Linux NVIDIA until proven otherwise.
