# SimLingo Sidecar Plan

- dry_run: `True`
- launch_mode: `manual_two_process_sidecar`
- route_count: `2`
- blockers: `3`
- simlingo_plan_path: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_command_plan.json`
- overlay_plan_path: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json`

## Commands

### simlingo_bench2drive

- cwd: `/Users/kenjipcx/SOTA/external/simlingo`
- start_after_s: `0.0`

```bash
python /Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py --routes=/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml --repetitions=1 --track=SENSORS --checkpoint=/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_outputs/res/seed_1_res.json --timeout=600 --agent=/Users/kenjipcx/SOTA/external/simlingo/team_code/agent_simlingo.py --agent-config=/workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt --traffic-manager-seed=1 --port=20000 --traffic-manager-port=10000
```

### driverx_overlay_injector

- cwd: `/Users/kenjipcx/SOTA/0xDriver`
- start_after_s: `5.0`

```bash
bash scripts/run_carla_client_docker.sh python -m driverx run-overlay-injection --config configs/carla_local.sample.yaml --plan /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-021/artifacts/qa/2026-05-04T220000Z/overlay-injection/overlay_injection_plan.json --output-root /Users/kenjipcx/SOTA/0xDriver/tickets/TASK-023/artifacts/qa/2026-05-05T053000Z/sidecar-plan/overlay-injection-run --run-id overlay-injection-run
```

## Blockers

- SimLingo live execution requires Linux NVIDIA; current platform is Darwin.
- CARLA 0.9.15 root not found: /Users/kenjipcx/software/carla0915
- SimLingo checkpoint not found: /workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt

## Notes

- This artifact is a launch plan, not a live process supervisor.
- Use it on the same machine/CARLA server that runs SimLingo.
- For stock SimLingo today, prefer an H100/H200 host; RTX PRO 6000 Blackwell needs a rebuild lane.
