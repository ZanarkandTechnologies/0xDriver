#!/usr/bin/env bash
set -euo pipefail
source "/workspace/conda/etc/profile.d/conda.sh"
conda activate "simlingo"
cd "/workspace/external/simlingo"
export CARLA_ROOT="/workspace/software/carla0915"
export WORK_DIR="/workspace/external/simlingo"
export SCENARIO_RUNNER_ROOT="/workspace/external/simlingo/Bench2Drive/scenario_runner"
export LEADERBOARD_ROOT="/workspace/external/simlingo/Bench2Drive/leaderboard"
export SAVE_PATH="/workspace/artifacts/task20/viz"
export PYTHONPATH="/workspace/external/simlingo:/workspace/software/carla0915/PythonAPI:/workspace/software/carla0915/PythonAPI/carla:/workspace/software/carla0915/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:/workspace/external/simlingo/Bench2Drive/scenario_runner:/workspace/external/simlingo/Bench2Drive/leaderboard:${PYTHONPATH:-}"
python -u "/workspace/external/simlingo/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py" \
  --routes="/workspace/external/simlingo/leaderboard/data/bench2drive_split/bench2drive_00.xml" \
  --repetitions=1 \
  --track=SENSORS \
  --checkpoint="/workspace/artifacts/task20/res/seed_1_res.json" \
  --timeout=600 \
  --agent="/workspace/external/simlingo/team_code/agent_simlingo.py" \
  --agent-config="/workspace/models/simlingo/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt" \
  --traffic-manager-seed=1 \
  --port=20000 \
  --traffic-manager-port=10000
