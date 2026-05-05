#!/usr/bin/env bash
set -euo pipefail
bash "/workspace/artifacts/task20/start_carla_server.sh"
trap 'bash "/workspace/artifacts/task20/stop_carla_server.sh"' EXIT
bash "/workspace/artifacts/task20/run_one_route.sh"
