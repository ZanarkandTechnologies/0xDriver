"""Scenario suite artifact writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driverx.scenarios.types import ScenarioRecipe, ScenarioSeed


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _recipe_table(recipes: list[ScenarioRecipe]) -> list[str]:
    lines = [
        "| recipe | parent seed | mutation | expected failure |",
        "|---|---|---|---|",
    ]
    for recipe in recipes:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(recipe.recipe_id),
                    _cell(recipe.parent_seed_id),
                    _cell(recipe.mutation),
                    _cell(recipe.expected_failure_mode),
                ]
            )
            + " |"
        )
    return lines


def write_scenario_suite(
    run_dir: Path,
    seeds: list[ScenarioSeed],
    recipes: list[ScenarioRecipe],
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    seed_payload = [seed.to_jsonable() for seed in seeds]
    recipe_payload = [recipe.to_jsonable() for recipe in recipes]
    recipes_path = run_dir / "scenario_recipes.json"
    report_path = run_dir / "scenario_suite_report.md"
    summary_path = run_dir / "scenario_suite_summary.json"
    recipes_path.write_text(json.dumps(recipe_payload, indent=2), encoding="utf-8")
    scenario_classes = sorted({seed.scenario_class for seed in seeds})
    mutation_counts: dict[str, int] = {}
    for recipe in recipes:
        mutation_counts[recipe.mutation] = mutation_counts.get(recipe.mutation, 0) + 1
    summary = {
        "num_seeds": len(seeds),
        "num_recipes": len(recipes),
        "scenario_classes": scenario_classes,
        "mutation_counts": dict(sorted(mutation_counts.items())),
        "seeds": seed_payload,
        "recipes_path": str(recipes_path),
        "report_path": str(report_path),
        "summary_path": str(summary_path),
    }
    lines = [
        "# Scenario Suite Report",
        "",
        "## Summary",
        "",
        f"- Seeds: `{len(seeds)}`",
        f"- Generated recipes: `{len(recipes)}`",
        f"- Scenario classes: `{', '.join(scenario_classes)}`",
        "",
        "## Generated Recipes",
        "",
        *_recipe_table(recipes),
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
