# SimLingo Command Plan

- cwd: `/Users/kenjipcx/SOTA/external/simlingo`
- dry_run: `True`
- readiness_blockers: `0`
- live_blockers: `3`

## Command

```bash
python /Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py --routes=/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/bench2drive_routes/generated_routes.xml --repetitions=1 --track=SENSORS --checkpoint=/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_outputs/res/seed_1_res.json --timeout=600 --agent=/Users/kenjipcx/SOTA/external/simlingo/team_code/agent_simlingo.py --agent-config=/workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt --traffic-manager-seed=1 --port=20000 --traffic-manager-port=10000
```

## Environment

- `CARLA_ROOT`: `/Users/kenjipcx/software/carla0915`
- `WORK_DIR`: `/Users/kenjipcx/SOTA/external/simlingo`
- `PYTHONPATH`: `/Users/kenjipcx/SOTA/external/simlingo:/Users/kenjipcx/software/carla0915/PythonAPI:/Users/kenjipcx/software/carla0915/PythonAPI/carla:/Users/kenjipcx/software/carla0915/carla:/Users/kenjipcx/software/carla0915/PythonAPI/carla/dist/carla-0.9.15-py3.8-linux-x86_64.egg:/Users/kenjipcx/software/carla0915/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:/Users/kenjipcx/software/carla0915/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:/Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/scenario_runner:/Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/leaderboard`
- `SCENARIO_RUNNER_ROOT`: `/Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/scenario_runner`
- `LEADERBOARD_ROOT`: `/Users/kenjipcx/SOTA/external/simlingo/Bench2Drive/leaderboard`
- `SAVE_PATH`: `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_outputs/viz`

## Expected Outputs

- `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_outputs/res/seed_1_res.json`
- `/Users/kenjipcx/SOTA/0xDriver/tickets/TASK-018/artifacts/qa/2026-05-04T210000Z/route-pack/simlingo_outputs/viz`

## Live Blockers

- SimLingo live execution requires Linux NVIDIA; current platform is Darwin.
- CARLA 0.9.15 root not found: /Users/kenjipcx/software/carla0915
- SimLingo checkpoint not found: /workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt
