#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
IMAGE="${CARLA_CLIENT_DOCKER_IMAGE:-python:3.10-bullseye}"
CARLA_PYTHON_VERSION="${CARLA_PYTHON_VERSION:-0.9.16}"

if [ "$#" -eq 0 ]; then
  echo "usage: scripts/run_carla_client_docker.sh <command...>" >&2
  echo "example: scripts/run_carla_client_docker.sh python -m driverx probe-carla --host host.docker.internal --port 2000" >&2
  exit 2
fi

docker run \
  --platform linux/amd64 \
  --rm \
  -e "CARLA_PYTHON_VERSION=${CARLA_PYTHON_VERSION}" \
  -e PIP_ROOT_USER_ACTION=ignore \
  -e PYTHONPATH=/workspace/src \
  -v "${ROOT}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  bash -lc 'python -m pip install --quiet --disable-pip-version-check "carla==${CARLA_PYTHON_VERSION}" && exec "$@"' \
  bash "$@"
