# GPU Host Suitability Report

- overall_state: `blocked`
- recommendation: Use a graphics-capable NVIDIA host with working Vulkan/OpenGL exposure for CARLA; avoid compute-only H100/H200 containers for closed-loop CARLA route proof.

## Blockers

- CARLA graphics runtime is blocked: Vulkan/graphics diagnostics or route logs show the server did not become reachable.

## Warnings

- Root disk is only 20GB; keep conda, CARLA, models, cache, and artifacts on a persistent workspace volume.

## Checks

| Check | Status | Summary |
| --- | --- | --- |
| `cuda_model` | `ready` | SimLingo torch stack supports sm_90 on NVIDIA H100 80GB HBM3. |
| `carla_graphics` | `blocked` | CARLA graphics runtime is blocked: Vulkan/graphics diagnostics or route logs show the server did not become reachable. |
| `host_storage` | `warning` | Root disk is only 20GB; keep conda, CARLA, models, cache, and artifacts on a persistent workspace volume. |
