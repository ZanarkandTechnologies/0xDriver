# driverx.assets

Generated asset planning for OOD CARLA scenarios.

## Rules

- Keep live 3D generation behind provider seams; local tests must not require API keys.
- Every asset must carry scale, collision proxy, semantic tags, source prompt,
  and license/source metadata before a scenario can reference it.
- Do not write downloaded/generated meshes into git-tracked paths.
