#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-root@31.22.104.74}"

ssh -o StrictHostKeyChecking=accept-new "${HOST}" 'set -euo pipefail
echo "HOST=$(hostname)"
echo "USER=$(whoami)"
echo "KERNEL=$(uname -srmo)"
echo "---GPU---"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
echo "---DISK---"
df -h /
echo "---MEM---"
free -h
echo "---TOOLS---"
for tool in python3 git wget curl rsync docker conda mamba vulkaninfo tmux screen; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf "%s=%s\n" "$tool" "$(command -v "$tool")"
  else
    printf "%s=\n" "$tool"
  fi
done
'
