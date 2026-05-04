#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-root@31.22.104.74}"
REMOTE_DIR="${2:-/workspace/0xDriver}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

ssh -o StrictHostKeyChecking=accept-new "${HOST}" "mkdir -p '${REMOTE_DIR}' /workspace/external /workspace/software /workspace/models /workspace/artifacts"

rsync -az --delete \
  --exclude='.git/' \
  --include='.env.example' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='data/' \
  --exclude='artifacts/' \
  --exclude='.venv/' \
  --exclude='.venv-*/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "${ROOT}/" "${HOST}:${REMOTE_DIR}/"

ssh "${HOST}" "cd '${REMOTE_DIR}' && /usr/bin/python3 -m compileall -q src tests && PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests"
