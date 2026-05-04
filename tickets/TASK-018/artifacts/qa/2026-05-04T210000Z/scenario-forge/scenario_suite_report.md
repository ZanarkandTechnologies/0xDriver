# Scenario Suite Report

## Summary

- Seeds: `3`
- Generated recipes: `2`
- Scenario classes: `Animals, CustomObstacles, PedestriansOnRoad`

## Generated Recipes

| recipe | parent seed | mutation | expected failure |
|---|---|---|---|
| generated-base-animals-0076-occlusion-000 | Base_Animals_0076 | occlusion | Policy commits before checking hidden cross-traffic or pedestrian emergence. |
| generated-generalization-customobstacles-1028-visual-noise-001 | Generalization_CustomObstacles_1028 | visual_noise | Policy overreacts to irrelevant visual artifact and leaves the route. |
