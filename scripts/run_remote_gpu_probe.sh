#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-${GPU_SSH_HOST:-root@31.22.104.74}}"
REMOTE_PROBE_DIR="${REMOTE_PROBE_DIR:-/workspace/artifacts/gpu-host-probe}"
LOCAL_PROBE_DIR="${LOCAL_PROBE_DIR:-tickets/TASK-029/artifacts/gpu-host-probe}"
SSH_OPTIONS="${GPU_SSH_OPTS:-}"
SSH_RSH="ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new"

ssh ${SSH_OPTIONS} -o StrictHostKeyChecking=accept-new "${HOST}" "set -euo pipefail
mkdir -p '${REMOTE_PROBE_DIR}'
cat > '${REMOTE_PROBE_DIR}/gpu_snapshot.txt' <<'SNAPSHOT_HEADER'
HOST=\$(hostname)
USER=\$(whoami)
KERNEL=\$(uname -srmo)
---GPU---
SNAPSHOT_HEADER
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader >> '${REMOTE_PROBE_DIR}/gpu_snapshot.txt' 2>/dev/null || true
{
  echo '---DISK---'
  df -h /
  echo '---MEM---'
  free -h || true
  echo '---TOOLS---'
  for tool in python3 git wget curl rsync docker conda mamba vulkaninfo tmux screen; do
    if command -v \"\${tool}\" >/dev/null 2>&1; then
      printf '%s=%s\n' \"\${tool}\" \"\$(command -v \"\${tool}\")\"
    else
      printf '%s=\n' \"\${tool}\"
    fi
  done
} >> '${REMOTE_PROBE_DIR}/gpu_snapshot.txt'

python3 - <<'PY' > '${REMOTE_PROBE_DIR}/torch_cuda_compatibility.json'
import json

payload = {
    'torch_imported': False,
    'cuda_available': False,
    'device_name': None,
    'device_capability': None,
    'required_arch': None,
    'compiled_arches': [],
    'compatible': False,
    'error': None,
}
try:
    import torch
    payload['torch_imported'] = True
    payload['torch_version'] = torch.__version__
    payload['torch_cuda'] = torch.version.cuda
    payload['compiled_arches'] = list(torch.cuda.get_arch_list()) if torch.cuda.is_available() else []
    payload['cuda_available'] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        major, minor = torch.cuda.get_device_capability(0)
        payload['device_name'] = torch.cuda.get_device_name(0)
        payload['device_capability'] = [major, minor]
        payload['required_arch'] = f'sm_{major}{minor}'
        payload['compatible'] = payload['required_arch'] in payload['compiled_arches']
except Exception as exc:
    payload['error'] = repr(exc)
print(json.dumps(payload, indent=2))
PY

{
  echo '# CARLA Runtime Diagnostics'
  echo
  echo '## Vulkan Default Devices'
  if command -v vulkaninfo >/dev/null 2>&1; then
    vulkaninfo --summary 2>&1 || true
  else
    echo 'vulkaninfo not installed'
  fi
  echo
  echo '## NVIDIA Vulkan ICD'
  if command -v vulkaninfo >/dev/null 2>&1 && [ -f /etc/vulkan/icd.d/nvidia_icd.json ]; then
    VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json vulkaninfo --summary 2>&1 || true
  else
    echo 'nvidia_icd.json or vulkaninfo not available'
  fi
} > '${REMOTE_PROBE_DIR}/carla_runtime_diagnostics.md'
"

mkdir -p "${LOCAL_PROBE_DIR}"
rsync -rltz --prune-empty-dirs \
  -e "${SSH_RSH}" \
  --no-owner \
  --no-group \
  --include='*/' \
  --include='gpu_snapshot.txt' \
  --include='torch_cuda_compatibility.json' \
  --include='carla_runtime_diagnostics.md' \
  --exclude='models/***' \
  --exclude='software/***' \
  --exclude='carla/***' \
  --exclude='.cache/***' \
  --exclude='*.tar' \
  --exclude='*.tar.gz' \
  --exclude='*.zip' \
  --exclude='*.pt' \
  --exclude='*.pth' \
  --exclude='*.ckpt' \
  --exclude='*.safetensors' \
  --exclude='*.mp4' \
  --exclude='*.avi' \
  --exclude='*.mov' \
  --exclude='*.png' \
  --exclude='*.jpg' \
  --exclude='*.jpeg' \
  --exclude='*' \
  "${HOST}:${REMOTE_PROBE_DIR%/}/" \
  "${LOCAL_PROBE_DIR}/"

echo "Pulled GPU host probe artifacts into ${LOCAL_PROBE_DIR}"
