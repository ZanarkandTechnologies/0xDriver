#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -eq 0 ]; then
  exec runuser -u "driverx" -- env HOME="/home/driverx" XDG_CONFIG_HOME="/home/driverx/.config" bash -c 'cd "${HOME}" && exec bash "/workspace/artifacts/task20/run_one_route_with_carla.sh"'
fi
exec bash "/workspace/artifacts/task20/run_one_route_with_carla.sh"
