# Git Hooks

These hooks are optional. `deep-init-project` scaffolds them so each repo has a
clear place for local quality gates, but nothing is enabled automatically.

## Recommended Default

Use `pre-push` for the heavier local gate:

- large-file scan: warn at `500` raw lines, block at `1000`
- project-owned local validators such as lint, typecheck, tests, and optional build
- optional soft heavy checks such as `desloppify`

Use `pre-commit` only when you explicitly want a smaller fast gate before each
commit.

## Activate

To make this repo use `.githooks/`:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
```

If you also want the optional pre-commit hook:

```bash
chmod +x .githooks/pre-commit
```

## Notes

- The sample hooks call repo-local validation scripts first:
  - `scripts/pre_commit_check.sh`
  - `scripts/pre_push_check.sh`
- `scripts/pre_push_check.sh` is the main policy surface. Put project-specific
  commands and exclusions there rather than expanding the hook itself.
- The `pre-push` hook then tries to run `coderabbit review` directly when the
  CLI is installed and authenticated.
- Utility-sharing warnings should stay advisory by default. Put the real shared
  utility placement convention in `PROJECT_RULES.md`.
- Override the review base branch with `CODERABBIT_BASE_BRANCH=<branch>` if the
  repo should not compare against the detected default or `main`.
- Remove or rename the hook files if the project should not use them.
