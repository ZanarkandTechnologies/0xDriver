# docker AGENTS.md

- Keep Docker images reproducible and scoped to one runtime boundary.
- Do not bake local data, credentials, generated artifacts, or model weights
  into images.
- Prefer mounted repo paths and environment-configured dataset/model locations.
- Keep GPU-specific serving images separate from the CPU Waymo parsing image
  unless a later ticket proves a shared image is simpler.
- Follow MEM-0008: official Waymo E2E dependencies live behind a Linux x86_64
  runtime boundary, with fixture/mock paths remaining dependency-light.
- Follow MEM-0016: local CARLA 0.9.16 client work uses the dedicated Linux
  amd64 `driverx-carla-client:0.9.16` image; keep this separate from future
  SimLingo/CUDA serving images.
- Do not auto-inject repo `.env` into Docker containers; use
  `DRIVERX_DOCKER_ENV_FILE` only when a command explicitly needs local env vars.
