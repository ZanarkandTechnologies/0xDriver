import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios import ScenarioRecipe, load_scenario_seeds
from driverx.simulators import (
    build_bench2drive_route_suite,
    compact_overlay_injection_summary,
    compile_overlay_injection_plan,
    write_bench2drive_route_suite,
    write_overlay_injection_plan,
)


FIXTURE_ROOT = Path("tests/fixtures/fail2drive_like")


def _write_route_pack(root: Path) -> Path:
    seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
    recipes = [
        ScenarioRecipe(
            recipe_id="generated-base-animals-occlusion",
            parent_seed_id=seeds[0].seed_id,
            mutation="occlusion",
            actors=[
                {
                    "role": "occluder",
                    "asset": "parked_vehicle_or_construction_barrier",
                    "placement": "before crossing point",
                }
            ],
            environment={"visibility": "partial", "occlusion": "high"},
            expected_failure_mode="hidden crossing hazard",
            memory_query=["occlusion", "creep"],
            route_path=seeds[0].route_path,
        ),
        ScenarioRecipe(
            recipe_id="generated-custom-obstacles-visual-noise",
            parent_seed_id=seeds[2].seed_id,
            mutation="visual_noise",
            actors=[
                {
                    "role": "distractor",
                    "asset": "high-contrast_image_or_signage",
                    "placement": "visible but outside drivable corridor",
                }
            ],
            environment={"texture_shift": "high", "weather": "neutral"},
            expected_failure_mode="overreacts to irrelevant visual artifact",
            memory_query=["visual_noise", "distractor", "route_relevance"],
            route_path=seeds[2].route_path,
        ),
    ]
    suite = build_bench2drive_route_suite(
        root / "route-pack",
        recipes,
        route_root=FIXTURE_ROOT,
        behavior_id="motorcycle_filtering",
    )
    summary = write_bench2drive_route_suite(root / "route-pack", suite)
    return Path(summary["manifest_path"])


class OverlayInjectionTest(unittest.TestCase):
    def test_compile_overlay_injection_plan_from_route_pack(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            route_pack = _write_route_pack(tmp_path)
            plan = compile_overlay_injection_plan(route_pack, tmp_path / "inject")
            summary = write_overlay_injection_plan(tmp_path / "inject", plan)
            compact = compact_overlay_injection_summary(summary)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["runtime_mode"], "dry_run_companion_plan")
        self.assertEqual(payload["num_routes"], 2)
        self.assertEqual(payload["validation_errors"], [])
        self.assertEqual(payload["routes"][0]["behavior_id"], "motorcycle_filtering")
        self.assertEqual(payload["routes"][0]["overlay_actors"][0]["role"], "occluder")
        self.assertEqual(payload["routes"][1]["overlay_actors"][0]["role"], "distractor")
        self.assertIn("route_suite_path", payload["routes"][0]["driverx_runtime_contract"][1])
        self.assertEqual(payload["routes"][0]["environment"]["occlusion"], "high")
        self.assertGreater(len(payload["routes"][0]["script_plan"]["ticks"]), 0)
        self.assertIn("route-pack/bench2drive_routes/000_", payload["routes"][0]["route_path"])
        self.assertIn("occlusion", payload["routes"][0]["memory_query"])
        first_companion = payload["routes"][0]["script_plan"]["actors"][2]
        second_companion = payload["routes"][1]["script_plan"]["actors"][2]
        self.assertEqual(first_companion["role"], "occluder")
        self.assertEqual(second_companion["role"], "distractor")
        self.assertNotEqual(first_companion["blueprint_filter"], second_companion["blueprint_filter"])
        self.assertNotEqual(
            payload["routes"][0]["script_plan"]["ticks"][0]["overlay_role"],
            payload["routes"][1]["script_plan"]["ticks"][0]["overlay_role"],
        )
        self.assertEqual(compact["routes"][0]["overlay_actor_count"], 1)
        self.assertEqual(compact["routes"][0]["overlay_roles"], ["occluder"])
        self.assertEqual(compact["routes"][1]["overlay_roles"], ["distractor"])
        self.assertEqual(compact["routes"][0]["tick_count"], 26)
        self.assertNotIn("ticks", json.dumps(compact))
        self.assertIn("static.prop.streetbarrier", report)
        self.assertIn("static.prop.trafficwarning", report)
        self.assertIn("Overlay Injection Plan", report)

    def test_compile_overlay_injection_plan_supports_behavior_override(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            route_pack = _write_route_pack(tmp_path)
            plan = compile_overlay_injection_plan(
                route_pack,
                tmp_path / "inject",
                behavior_id="sudden_brake",
            )

        self.assertEqual([route.behavior_id for route in plan.routes], ["sudden_brake", "sudden_brake"])
        self.assertTrue(all(route.script_plan.behavior_id == "sudden_brake" for route in plan.routes))

    def test_compile_overlay_injection_plan_rejects_unknown_behavior(self) -> None:
        with TemporaryDirectory() as tmp:
            route_pack = _write_route_pack(Path(tmp))

            with self.assertRaisesRegex(ValueError, "Unsupported behavior_id"):
                compile_overlay_injection_plan(
                    route_pack,
                    Path(tmp) / "inject",
                    behavior_id="teleporting_scooter",
                )

    def test_compile_overlay_injection_plan_flags_contract_drift(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            route_pack = _write_route_pack(tmp_path)
            manifest = json.loads(route_pack.read_text(encoding="utf-8"))
            overlay_path = Path(manifest["exports"][0]["overlay_path"])
            overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
            overlay["driverx_runtime_contract"] = ["stale contract"]
            overlay_path.write_text(json.dumps(overlay), encoding="utf-8")

            plan = compile_overlay_injection_plan(route_pack, tmp_path / "inject")

        self.assertIn("driverx_runtime_contract drifted", plan.routes[0].validation_errors[0])
        self.assertEqual(plan.routes[1].validation_errors, [])


if __name__ == "__main__":
    unittest.main()
