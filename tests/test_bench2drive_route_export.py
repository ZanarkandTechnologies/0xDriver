import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree

from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators import (
    build_bench2drive_route_suite,
    resolve_recipe_route_path,
    write_bench2drive_route_suite,
)


FIXTURE_ROOT = Path("tests/fixtures/fail2drive_like")


class Bench2DriveRouteExportTest(unittest.TestCase):
    def _recipe(self):
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
        return generate_scenario_recipes(
            [seeds[0]],
            MutationPolicy(mutations=("regional_driving_behavior",)),
            count=1,
            random_seed=4,
        )[0]

    def test_resolve_recipe_route_path_uses_route_root(self) -> None:
        route_path = resolve_recipe_route_path(self._recipe(), FIXTURE_ROOT)

        self.assertEqual(route_path.name, "Base_Animals_0076.xml")

    def test_build_route_suite_writes_xml_and_overlay(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            suite = build_bench2drive_route_suite(
                run_dir,
                [self._recipe()],
                route_root=FIXTURE_ROOT,
                behavior_id="motorcycle_filtering",
            )
            summary = write_bench2drive_route_suite(
                run_dir,
                suite,
                simlingo_plan={"json_path": str(run_dir / "simlingo_command_plan.json")},
            )

            route_root = ElementTree.parse(suite.route_suite_path).getroot()
            overlay = json.loads(suite.exports[0].overlay_path.read_text(encoding="utf-8"))
            manifest = json.loads(Path(summary["manifest_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(route_root.tag, "routes")
        self.assertEqual(route_root.find("route").attrib["id"], "0076")
        self.assertEqual(suite.exports[0].town_name, "Town12")
        self.assertEqual(overlay["behavior_id"], "motorcycle_filtering")
        self.assertEqual(overlay["recipe"]["mutation"], "regional_driving_behavior")
        self.assertIn("sidecar_overlay", overlay["injection_strategy"])
        self.assertEqual(manifest["num_routes"], 1)
        self.assertIn("Bench2Drive Route Pack", report)

    def test_build_route_suite_merges_multiple_recipes_in_order(self) -> None:
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
        recipes = generate_scenario_recipes(
            seeds[:2],
            MutationPolicy(mutations=("occlusion",)),
            count=2,
            random_seed=4,
        )
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            suite = build_bench2drive_route_suite(
                run_dir,
                recipes,
                route_root=FIXTURE_ROOT,
                behavior_id="motorcycle_filtering",
            )
            summary = write_bench2drive_route_suite(run_dir, suite)
            route_root = ElementTree.parse(suite.route_suite_path).getroot()
            manifest = json.loads(Path(summary["manifest_path"]).read_text(encoding="utf-8"))
            overlays = [
                json.loads(export.overlay_path.read_text(encoding="utf-8"))
                for export in suite.exports
            ]
            route_file_count = len(list((run_dir / "bench2drive_routes").glob("*.xml")))
            overlay_file_count = len(list((run_dir / "driverx_overlays").glob("*.json")))

        routes = route_root.findall("route")
        self.assertEqual([route.attrib["id"] for route in routes], ["0076", "1088"])
        self.assertEqual([export.recipe_id for export in suite.exports], [recipe.recipe_id for recipe in recipes])
        self.assertEqual(route_file_count, 3)
        self.assertEqual(overlay_file_count, 2)
        self.assertEqual(manifest["num_routes"], 2)
        self.assertEqual(manifest["exports"][1]["route_id"], "1088")
        self.assertIn("single-recipe replay", overlays[0]["driverx_runtime_contract"][0])
        self.assertIn("suite execution", overlays[0]["driverx_runtime_contract"][1])

    def test_missing_route_path_is_actionable(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Route XML not found"):
            resolve_recipe_route_path(self._recipe(), Path("missing-route-root"))


if __name__ == "__main__":
    unittest.main()
