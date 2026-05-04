# TASK-017 QA Report

- Remote GPU: `NVIDIA RTX PRO 6000 Blackwell Server Edition`
- Torch: `2.2.0+cu121` CUDA `12.1`
- Required arch: `sm_120`
- Compiled arches: `sm_50, sm_60, sm_70, sm_75, sm_80, sm_86, sm_90`
- Compatible: `False`
- SimLingo commit: `743b243afd6cf5ff51b9fa1f8cac86f22d569684`
- Model revision: `26c7c89e797d4e25bbf640013317af8da26a5454`
- Checkpoint SHA256: `ec8943723d266ee9f5f56f45d153a163b22616960bfccb741965ea5daa700d28`
- Route: `RouteScenario_1711_rep0` / `ParkingCutIn_1` / `Town12`
- Result: `Failed - Agent crashed`, route score `0`, driving score `0.0`

## Blocker

PyTorch 2.2.0+cu121 does not include sm_120 kernels for RTX PRO 6000 Blackwell; first SimLingo tick crashes with CUDA no kernel image available.

The PTX retry did not bypass the issue: CUDA_FORCE_PTX_JIT=1 reproduced the same CUDA no-kernel-image crash.

## Evidence Files

- `remote_snapshot.txt`
- `torch_cuda_compatibility.json`
- `simlingo_readiness.json`
- `simlingo_command_plan.json`
- `run_one_route.log`
- `run_one_route_ptx.log`
- `seed_1_res.json`
- `seed_1_res_ptx.json`

