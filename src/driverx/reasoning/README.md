# Reasoning

## Purpose

Convert scene context into validated structured driving intent.

## Public API

- `build_reasoner(config)`
- `MockReasoner`
- `intent_from_mapping(payload)`

## Minimal Example

```python
from driverx.reasoning.mock import MockReasoner

intent = MockReasoner().infer_intent(frame)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_reasoning_schema
```
