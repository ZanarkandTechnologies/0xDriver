# Planning

## Purpose

Turn structured intent into candidate trajectories, combine them with local
motion priors, smooth them, and rank the best prediction. Also provide simple
non-VLA rule baselines for experiment comparison.

## Public API

- `generate_candidates(frame, intent)`
- `generate_hybrid_candidates(frame, intent)`
- `generate_rule_baselines(frame)`
- `smooth_candidate(candidate)`
- `rank_candidates(frame, candidates)`

## Minimal Example

```python
from driverx.planning import generate_hybrid_candidates, rank_candidates, smooth_candidate

candidates = [smooth_candidate(c) for c in generate_hybrid_candidates(frame, intent)]
selected = rank_candidates(frame, candidates)
rule_baselines = [smooth_candidate(c) for c in generate_rule_baselines(frame)]
```

## Test

```bash
PYTHONPATH=src python3 -m unittest tests.test_trajectory
```
