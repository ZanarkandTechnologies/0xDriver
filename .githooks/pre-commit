#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
CHECK_SCRIPT="$ROOT/scripts/pre_commit_check.sh"

if [ ! -f "$CHECK_SCRIPT" ]; then
  echo "Skip pre-commit checks: missing $CHECK_SCRIPT" >&2
  exit 0
fi

bash "$CHECK_SCRIPT"
