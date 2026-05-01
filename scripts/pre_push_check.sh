#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"

WARN_THRESHOLD="${PRE_PUSH_WARN_LINES:-500}"
BLOCK_THRESHOLD="${PRE_PUSH_BLOCK_LINES:-1000}"

# Fill these in for the project during bootstrap follow-through.
LINT_CMD="${PRE_PUSH_LINT_CMD:-}"
TYPECHECK_CMD="${PRE_PUSH_TYPECHECK_CMD:-}"
TEST_CMD="${PRE_PUSH_TEST_CMD:-}"
BUILD_CMD="${PRE_PUSH_BUILD_CMD:-}"
DESLOPPIFY_CMD="${PRE_PUSH_DESLOPPIFY_CMD:-}"

warn_tmp="$(mktemp)"
block_tmp="$(mktemp)"
utility_tmp="$(mktemp)"
cleanup() {
  rm -f "$warn_tmp" "$block_tmp" "$utility_tmp"
}
trap cleanup EXIT

is_excluded_path() {
  case "$1" in
    .git/*|.harness/*|.next/*|dist/*|build/*|coverage/*|out/*|tmp/*|temp/*|vendor/*|third_party/*|node_modules/*|.turbo/*|.cache/*|.desloppify/*|generated/*|__generated__/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_source_file() {
  case "$1" in
    *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.py|*.go|*.rs|*.java|*.kt|*.swift|*.rb|*.php|*.sh|*.bash|*.zsh|*.css|*.scss|*.sass|*.vue|*.svelte|*.c|*.cc|*.cpp|*.h|*.hpp|*.cs)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

collect_source_file_sizes() {
  while IFS= read -r -d '' path; do
    is_excluded_path "$path" && continue
    is_source_file "$path" || continue

    lines="$(wc -l <"$ROOT/$path" | tr -d ' ')"

    if [ "$lines" -ge "$BLOCK_THRESHOLD" ]; then
      printf '%s\t%s\n' "$lines" "$path" >>"$block_tmp"
    elif [ "$lines" -ge "$WARN_THRESHOLD" ]; then
      printf '%s\t%s\n' "$lines" "$path" >>"$warn_tmp"
    fi

    base_name="$(basename "$path")"
    stem="${base_name%.*}"
    case "$stem" in
      helper|helpers|util|utils|common|shared)
        case "$path" in
          */utils/*|*/shared/*|*/common/*)
            ;;
          *)
            printf '%s\t%s\n' "$lines" "$path" >>"$utility_tmp"
            ;;
        esac
        ;;
    esac
  done < <(git -C "$ROOT" ls-files -z)
}

print_ranked_list() {
  local heading="$1"
  local file="$2"

  [ -s "$file" ] || return 0

  echo "$heading"
  sort -t "$(printf '\t')" -k1,1nr -k2,2 "$file" | while IFS=$'\t' read -r lines path; do
    printf '  - %s lines :: %s\n' "$lines" "$path"
  done
}

run_check() {
  local label="$1"
  local command_string="$2"

  if [ -z "$command_string" ]; then
    echo "Skip $label: command not configured in scripts/pre_push_check.sh"
    return 0
  fi

  echo "Run $label"
  bash -lc "$command_string"
}

collect_source_file_sizes

if [ -s "$warn_tmp" ]; then
  print_ranked_list "Warn: large tracked source files detected" "$warn_tmp"
fi

if [ -s "$utility_tmp" ]; then
  echo "Warn: helper-style files detected outside the preferred shared utility surface"
  sort -t "$(printf '\t')" -k1,1nr -k2,2 "$utility_tmp" | while IFS=$'\t' read -r lines path; do
    printf '  - %s lines :: %s\n' "$lines" "$path"
  done
  echo "  Review whether these belong in the shared utility location declared in PROJECT_RULES.md."
fi

if [ -s "$block_tmp" ]; then
  print_ranked_list "Fail: oversized tracked source files detected" "$block_tmp"
  echo "Suggested next step:"
  echo "  codex \"refactor the oversized files above so each falls below ${BLOCK_THRESHOLD} raw lines and reuse shared utilities instead of duplicating helpers\""
  exit 1
fi

run_check "lint" "$LINT_CMD"
run_check "typecheck" "$TYPECHECK_CMD"
run_check "tests" "$TEST_CMD"
run_check "build" "$BUILD_CMD"
run_check "desloppify" "$DESLOPPIFY_CMD"

echo "Pre-push checks passed."
