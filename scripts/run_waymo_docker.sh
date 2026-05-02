#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  set -- python -m driverx inspect-scene --config configs/waymo_local.sample.yaml --run-id waymo-docker-smoke
fi

HOST_ROOT="$(pwd)"
if [[ -z "${WAYMO_E2E_TFRECORD:-}" ]]; then
  export WAYMO_E2E_TFRECORD="/workspace/data/val_202504211843.tfrecord-00000-of-00093"
elif [[ "${WAYMO_E2E_TFRECORD}" == "${HOST_ROOT}"/* ]]; then
  export WAYMO_E2E_TFRECORD="/workspace/${WAYMO_E2E_TFRECORD#"${HOST_ROOT}/"}"
elif [[ "${WAYMO_E2E_TFRECORD}" != /* ]]; then
  export WAYMO_E2E_TFRECORD="/workspace/${WAYMO_E2E_TFRECORD}"
fi

docker run --rm \
  --platform linux/amd64 \
  -e WAYMO_E2E_TFRECORD="${WAYMO_E2E_TFRECORD}" \
  -v "$(pwd)":/workspace \
  -w /workspace \
  driverx-waymo:local \
  "$@"
