# driverx.policies

## Purpose

Owns the runtime boundary between generated CARLA scenarios and autonomy
policies. The same interface can wrap mock policies, deterministic local
fallbacks, API VLMs, SimLingo/CarLLaVA, or Alpamayo later.

## Public API

- `PolicyContext`
- `PolicyDecision`
- `select_policy_adapter(name, memory_aware=False)`
- `run_policy_fixture(...)`
- `write_policy_decision(...)`

## Example

```bash
PYTHONPATH=src python3 -m driverx run-policy-fixture --policy mock --run-id task13-policy
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_policies
```
