# Blockers

Live blocker ledger for long-running 0xDriver execution. Add blockers here when
work cannot proceed inside the current ticket, then continue to the next
unblocked ticket when possible.

## Open

- None currently.

## Resolved

- 2026-05-05 15:19 +0800 | runpod,ssh | RunPod SSH initially rejected
  local keys because `/root/.ssh/authorized_keys` split the public key over two
  lines. Fixed by replacing it with one single-line `ssh-ed25519 ... runpod`
  entry; direct TCP SSH now works.
