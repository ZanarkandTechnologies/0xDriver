"""Deterministic OOD recipe generation from scenario seeds."""

from __future__ import annotations

import random
import re
from typing import Any

from driverx.scenarios.types import MutationPolicy, ScenarioRecipe, ScenarioSeed


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _mutation_payload(seed: ScenarioSeed, mutation: str) -> dict[str, Any]:
    base_query = [seed.scenario_class, *seed.ood_tags, mutation]
    if mutation == "obstacle_substitution":
        return {
            "actors": [
                {
                    "role": "unexpected_obstacle",
                    "asset": "animal_or_debris_proxy",
                    "placement": "near ego route centerline",
                }
            ],
            "environment": {"visibility": "clear", "surface": "dry"},
            "expected_failure_mode": "Policy treats unfamiliar object as visual noise instead of occupied space.",
            "memory_query": [*base_query, "occupied_space", "unknown_object"],
        }
    if mutation == "occlusion":
        return {
            "actors": [
                {
                    "role": "occluder",
                    "asset": "parked_vehicle_or_construction_barrier",
                    "placement": "before crossing point",
                }
            ],
            "environment": {"visibility": "partial", "occlusion": "high"},
            "expected_failure_mode": "Policy commits before checking hidden cross-traffic or pedestrian emergence.",
            "memory_query": [*base_query, "hidden_hazard", "creep"],
        }
    if mutation == "visual_noise":
        return {
            "actors": [
                {
                    "role": "distractor",
                    "asset": "high-contrast_image_or_signage",
                    "placement": "visible but outside drivable corridor",
                }
            ],
            "environment": {"texture_shift": "high", "weather": "neutral"},
            "expected_failure_mode": "Policy overreacts to irrelevant visual artifact and leaves the route.",
            "memory_query": [*base_query, "distractor", "route_relevance"],
        }
    if mutation == "lane_blockage":
        return {
            "actors": [
                {
                    "role": "blocker",
                    "asset": "stalled_vehicle_or_barrier",
                    "placement": "blocking current lane with partial bypass available",
                }
            ],
            "environment": {"lane_availability": "partial", "traffic": "light"},
            "expected_failure_mode": "Policy either freezes despite a safe bypass or drives into blocked space.",
            "memory_query": [*base_query, "blocked_lane", "local_bypass"],
        }
    if mutation == "regional_driving_behavior":
        return {
            "actors": [
                {
                    "role": "two_wheeler",
                    "asset": "motorcycle_filtering_or_scooter",
                    "placement": "adjacent lane gap",
                }
            ],
            "environment": {"traffic_style": "dense_asian_urban", "lane_discipline": "low"},
            "expected_failure_mode": "Policy assumes lane-disciplined traffic and misses lateral filtering behavior.",
            "memory_query": [*base_query, "motorcycle_filtering", "lateral_uncertainty"],
        }
    return {
        "actors": [
            {
                "role": "generic_shift",
                "asset": "unfamiliar_object",
                "placement": "near route",
            }
        ],
        "environment": {"shift": mutation},
        "expected_failure_mode": "Policy fails to separate route-relevant hazards from harmless novelty.",
        "memory_query": base_query,
    }


def generate_scenario_recipes(
    seeds: list[ScenarioSeed],
    mutation_policy: MutationPolicy,
    count: int,
    random_seed: int,
) -> list[ScenarioRecipe]:
    if count <= 0:
        raise ValueError("count must be positive.")
    if not seeds:
        raise ValueError("At least one ScenarioSeed is required.")
    rng = random.Random(random_seed)
    ordered_seeds = sorted(seeds, key=lambda seed: seed.seed_id)
    recipes: list[ScenarioRecipe] = []
    for index in range(count):
        seed = ordered_seeds[index % len(ordered_seeds)]
        mutation = rng.choice(mutation_policy.mutations)
        payload = _mutation_payload(seed, mutation)
        recipe_id = f"generated-{_slug(seed.seed_id)}-{_slug(mutation)}-{index:03d}"
        recipes.append(
            ScenarioRecipe(
                recipe_id=recipe_id,
                parent_seed_id=seed.seed_id,
                mutation=mutation,
                actors=list(payload["actors"]),
                environment=dict(payload["environment"]),
                expected_failure_mode=str(payload["expected_failure_mode"]),
                memory_query=[str(value) for value in payload["memory_query"]],
                route_path=seed.route_path,
            )
        )
    return recipes
