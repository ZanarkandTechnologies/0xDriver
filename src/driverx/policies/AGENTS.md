# driverx.policies

Policy adapter boundary for frozen VLA/VLM, mock, and deterministic fallback
policies.

## Rules

- Real model adapters must fail with setup guidance when credentials,
  checkpoints, or runtime dependencies are missing.
- Local tests must run through mock or deterministic adapters only.
- Adapter outputs must include structured intent/action, latency, reason summary,
  and memory ids when memory was injected.
