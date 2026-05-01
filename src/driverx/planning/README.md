# Planning

## Purpose

Turn structured intent into candidate trajectories, smooth them, and rank the
best prediction.

## Public API

- `generate_candidates(frame, intent)`
- `smooth_candidate(candidate)`
- `rank_candidates(frame, candidates)`

## Minimal Example

```python
candidates = [smooth_candidate(c) for c in generate_candidates(frame, intent)]
selected = rank_candidates(frame, candidates)
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_trajectory
```
