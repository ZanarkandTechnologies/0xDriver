# TASK-017: Remote GPU SimLingo One-Route Proof

## Status
- state: done
- owner: Codex
- assignee: generalPurpose
- dependencies: RTX PRO 6000 SSH host, Hugging Face token, remote sudo/root
- location: scripts/, configs/, src/driverx/simulators, remote `/workspace`
- enter when: Prime Intellect GPU SSH access is available
- leave when: stock SimLingo + CARLA 0.9.15 produces one closed-loop route
  result or a precise runtime blocker with artifacts
- blockers: RTX PRO 6000 Blackwell `sm_120` is incompatible with stock
  SimLingo's pinned `torch==2.2.0+cu121` wheel, which only ships kernels
  through `sm_90`; route reaches first agent tick, then crashes with
  `CUDA error: no kernel image is available for execution on the device`.
- spawned follow-ups: TASK-018 generated OOD route execution; TASK-019 SimLingo
  result ingestion; TASK-020 CARLA 0.9.16 port attempt
- complexity: L

### Summary
Bootstrap the rented Linux NVIDIA host as the first real closed-loop VLA runtime.
The target proof is a stock SimLingo/Bench2Drive route with CARLA 0.9.15,
checkpoint access, result JSON, RGB/viz outputs, and enough logs to decide the
next integration step.

### Scope
In scope:

- Remote GPU snapshot and runtime prerequisites.
- Sync this local 0xDriver workspace to the GPU host without datasets,
  artifacts, model weights, or secrets.
- Clone/update external SimLingo checkout on the GPU host.
- Install CARLA 0.9.15 and AdditionalMaps.
- Install a SimLingo Python environment.
- Download the SimLingo checkpoint/model assets.
- Run one Bench2Drive route through SimLingo or capture a precise blocker.
- Write local/remote progress and QA artifacts.

Out of scope:

- Meshy/3D asset generation.
- Training or fine-tuning.
- Full 220-route Bench2Drive evaluation.
- CARLA 0.9.16 SimLingo porting.
- FlashDrive-style serving acceleration.

### Plan

#### Change
Create a reproducible remote execution lane for stock SimLingo closed-loop
driving.

#### Why
The submission needs real simulator behavior evidence. The existing repo proves
scenario generation, memory, policy contracts, and local CARLA smoke paths, but
only the GPU box can prove the VLA policy running in closed loop.

#### Before -> After
- Before: SimLingo command plans and setup blockers only.
- After: remote runtime snapshot, installed CARLA/SimLingo stack, one-route
  result or exact blocker, and artifacts ready for ingestion.

#### Touch
- `tickets/TASK-017/ticket.md`
- `scripts/sync_remote_gpu.sh`
- `scripts/remote_gpu_snapshot.sh`
- `scripts/remote_simlingo_bootstrap.sh`
- later if needed: `src/driverx/simulators/simlingo.py`
- later if needed: `configs/simlingo.gpu.sample.yaml`

#### Inspect
- `../external/simlingo/README.md`
- `../external/simlingo/setup_carla.sh`
- `../external/simlingo/environment.yaml`
- `../external/simlingo/Bench2Drive/README.md`
- `../external/simlingo/Bench2Drive/leaderboard/scripts/run_evaluation_debug.sh`

#### Signature delta
```bash
scripts/remote_gpu_snapshot.sh [host]
scripts/sync_remote_gpu.sh [host] [remote_dir]
scripts/remote_simlingo_bootstrap.sh
```

Future Python ingestion seam:

```python
parse_simlingo_result(path: Path) -> SimLingoRunRecord
write_closed_loop_report(record: SimLingoRunRecord, run_dir: Path) -> dict
```

#### Type Sketch
```python
RemoteGpuSnapshot = {
  "host": str,
  "gpu": str,
  "vram_mb": int,
  "driver": str,
  "disk_free_gb": float,
  "ram_gb": float,
  "docker": bool,
  "conda": bool,
  "vulkaninfo": bool,
}

SimLingoRunRecord = {
  "route": str,
  "checkpoint": str,
  "result_json": str,
  "viz_dir": str,
  "success": bool | None,
  "driving_score": float | None,
  "route_completion": float | None,
  "infractions": list[str],
  "blocker": str | None,
}
```

#### Typed flow example
`ssh root@31.22.104.74` -> snapshot -> `/workspace/0xDriver` sync ->
`/workspace/external/simlingo` clone -> CARLA 0.9.15 install ->
`conda activate simlingo` -> checkpoint download -> one Bench2Drive route ->
`artifacts/remote/task17/...` result pointers.

#### Execution steps
1. Capture remote GPU snapshot.
2. Sync repo to `/workspace/0xDriver`.
3. Install apt runtime dependencies and Miniforge when missing.
4. Clone/update SimLingo under `/workspace/external/simlingo`.
5. Install CARLA 0.9.15 plus AdditionalMaps under `/workspace/software/carla0915`.
6. Create/update the `simlingo` conda env.
7. Download SimLingo model checkpoint from Hugging Face.
8. Generate a dry-run plan using 0xDriver on the remote host.
9. Run a one-route Bench2Drive/SimLingo evaluation.
10. Generate video if RGB frames exist.
11. Pull or summarize result artifacts back into TASK-017 evidence.
12. Run review and QA; commit local helper/ticket changes.

#### Recommendation
Prove stock SimLingo on CARLA 0.9.15 first. Accept the tradeoff that the first
GPU proof is not using our generated OOD scenarios yet; it de-risks the hardest
runtime before adding generation.

#### Options considered
- Stock SimLingo 0.9.15 first: fastest trustworthy closed-loop proof.
- Force CARLA 0.9.16 first: aligns with local Mac install, but risks route/API
  drift before any VLA evidence exists.
- Skip SimLingo and run image-only VQA: easiest setup, but weaker and not a
  true driving-policy demo.

#### Blast radius
- Remote apt/conda/pip installs affect only the rented GPU host.
- Local changes are scripts/docs/ticket surfaces.
- No datasets, model weights, generated videos, or secrets are committed.

#### Risks
- CARLA headless Vulkan launch may fail.
- SimLingo environment may conflict with Blackwell/CUDA driver versions.
- Hugging Face checkpoint path may differ from the assumed repo layout.
- The prepared runtime now has about `91G` free after CARLA, AdditionalMaps,
  SimLingo, and checkpoint setup; preserve it for handoff, but use a larger
  disk if running many routes or caching additional model assets.

### Acceptance Criteria
- [x] AC-1: Remote GPU snapshot captured with GPU, driver, RAM, disk, and tool
  availability.
- [x] AC-2: 0xDriver workspace synced to remote without ignored heavy assets or
  secrets.
- [x] AC-3: SimLingo checkout exists remotely and required files are present.
- [x] AC-4: CARLA 0.9.15 exists remotely or the exact download/install blocker
  is recorded.
- [x] AC-5: SimLingo environment exists remotely or the exact environment
  blocker is recorded.
- [x] AC-6: SimLingo checkpoint exists remotely or the exact model-access
  blocker is recorded.
- [x] AC-7: One Bench2Drive route runs to result JSON/video, or the exact
  runtime blocker is recorded with logs.
- [x] AC-8: Local pre-push checks pass for helper/ticket changes.

### Verification
- `bash scripts/remote_gpu_snapshot.sh root@31.22.104.74`
- `bash scripts/sync_remote_gpu.sh root@31.22.104.74 /workspace/0xDriver`
- remote `bash /workspace/0xDriver/scripts/remote_simlingo_bootstrap.sh`
- remote `python -m driverx inspect-simlingo`
- remote `python -m driverx plan-simlingo-run`
- remote one-route evaluation command
- `bash scripts/pre_push_check.sh`

### Autonomy Readiness
- SSH host: `root@31.22.104.74`
- Root/sudo: available.
- Disk: QA snapshot after bootstrap and route attempts shows `91G` free on
  `/workspace`; enough to preserve this prepared runtime but not enough for
  large multi-route cached runs.
- HF token: available locally in ignored `.env`; do not print or commit.
- Human gates: only needed for SSH failure, provider billing decisions,
  checkpoint license/access denial, or destructive instance changes.

### Evidence
- Remote snapshot: RTX PRO 6000 Blackwell Server Edition, 97887 MiB VRAM,
  driver 580.126.09, `91G` free disk at QA capture, 88GiB RAM, Docker/Git/Wget/
  Rsync/tmux/Conda/Vulkaninfo present; Mamba absent.
- Remote tmux/log path: `/workspace/artifacts/task17/bootstrap.log`,
  `/workspace/artifacts/task17/run_one_route.log`,
  `/workspace/artifacts/task17/run_one_route_ptx.log`.
- Install log: captured in local QA artifact
  `tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/remote_snapshot.txt` and
  remote `/workspace/artifacts/task17/bootstrap.log`.
- SimLingo checkout: commit `743b243afd6cf5ff51b9fa1f8cac86f22d569684`.
- Model revision: Hugging Face revision
  `26c7c89e797d4e25bbf640013317af8da26a5454`; checkpoint SHA256
  `ec8943723d266ee9f5f56f45d153a163b22616960bfccb741965ea5daa700d28`.
- CARLA proof: evaluator launched CARLA 0.9.15, `load_world success`, and
  `traffic_manager init success` for `RouteScenario_1711` in `Town12`.
- One-route result:
  `tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/seed_1_res.json` records
  `RouteScenario_1711_rep0`, `ParkingCutIn_1`, status
  `Failed - Agent crashed`, route completion `0`.
- Video/frame output: none; the agent crashed at the first model tick before
  `SAVE_PATH` frames were written.
- QA report:
  `tickets/TASK-017/artifacts/qa/2026-05-04T194700Z/report.md`.

### Blockers
- Initial `apt-get update` hung on the remote host; bootstrap now bounds apt
  setup and continues to Miniforge/CARLA/SimLingo until a concrete runtime
  blocker appears.
- First route attempt passed CARLA startup and traffic manager initialization
  but failed on `ModuleNotFoundError: team_code.config_simlingo`; fixed by
  prepending the SimLingo checkout root to live `PYTHONPATH`.
- Stock SimLingo then reached `> Running the route` and first agent tick, but
  crashed at `processed_image.to(self.device).bfloat16()` with
  `CUDA error: no kernel image is available for execution on the device`.
- `torch_cuda_compatibility.json` explains why: RTX PRO 6000 Blackwell requires
  `sm_120`, while `torch==2.2.0+cu121` in the upstream Python 3.8 environment
  ships `sm_50`, `sm_60`, `sm_70`, `sm_75`, `sm_80`, `sm_86`, and `sm_90`.
- `CUDA_FORCE_PTX_JIT=1` reproduced the same no-kernel-image crash, so PTX JIT
  is not a viable escape on this host.
- Recommended runtime follow-up: rerun the same synced stack on H100/H200
  (`sm_90`) or open a separate heavy porting ticket to rebuild PyTorch/CARLA
  around a Blackwell-compatible Python/CUDA stack.
