#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
CHECK_SCRIPT="$ROOT/scripts/pre_push_check.sh"

if [ -f "$CHECK_SCRIPT" ]; then
  bash "$CHECK_SCRIPT"
else
  echo "Skip pre-push checks: missing $CHECK_SCRIPT" >&2
fi

if ! command -v coderabbit >/dev/null 2>&1; then
  echo "Skip CodeRabbit pre-push: coderabbit CLI not found on PATH" >&2
  exit 0
fi

if ! coderabbit auth status >/dev/null 2>&1; then
  echo "Skip CodeRabbit pre-push: coderabbit CLI is not authenticated" >&2
  exit 0
fi

BASE_BRANCH="${CODERABBIT_BASE_BRANCH:-}"

if [ -z "$BASE_BRANCH" ]; then
  if origin_head="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null)"; then
    BASE_BRANCH="${origin_head##*/}"
  else
    BASE_BRANCH="main"
  fi
fi

coderabbit review --plain --type committed --base "$BASE_BRANCH"
