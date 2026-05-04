# SimLingo Result Report

- status: `Failed`
- success: `False`
- route_count: `1`
- progress: `1` / `1`
- route_completion: `0.0`
- driving_score: `0.0`
- infraction_penalty: `1.0`
- primary_route: `RouteScenario_1711_rep0`
- primary_scenario: `ParkingCutIn_1`
- primary_town: `Town12`
- exception: `RouteScenario_1711_rep0: Failed - Agent crashed`

## Blocker

CUDA no-kernel-image at first model tick; required `sm_120`, compiled arches `['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']`

## CUDA Compatibility

- device: `NVIDIA RTX PRO 6000 Blackwell Server Edition`
- torch: `2.2.0+cu121`
- required_arch: `sm_120`
- compiled_arches: `['sm_50', 'sm_60', 'sm_70', 'sm_75', 'sm_80', 'sm_86', 'sm_90']`
- compatible: `False`

## Route Log Signals

- `load_world success`: `True`
- `traffic_manager init success`: `True`
- `> Running the route`: `True`
- `CUDA error: no kernel image is available for execution on the device`: `True`
