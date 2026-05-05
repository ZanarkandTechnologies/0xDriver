# RAG Policy Comparison

- scenario_id: `construction_merge::motorcycle_filtering`
- policy: `mock`
- behavior_id: `motorcycle_filtering`
- live_model_claim: `False`
- notes: memory improved the mock policy outcome

## Improvement

- `success_proxy_delta`: `1`
- `driving_score_delta`: `37.0`
- `route_completion_delta`: `0.21`
- `infraction_delta`: `-2`

## Runs

### policy

- success_proxy: `False`
- driving_score: `58.0`
- route_completion: `0.74`
- latency_ms: `0.0204`
- retrieved_memory_ids: ``
- infractions: `too_fast_near_lateral_ood_actor, no_memory_for_regional_lateral_behavior`

### policy+memory

- success_proxy: `True`
- driving_score: `95.0`
- route_completion: `0.95`
- latency_ms: `0.0153`
- retrieved_memory_ids: `mem-sample-motorcycle-filtering`
- infractions: ``
