import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.memory import build_memory_bank, retrieve_memory, write_memory_bank
from driverx.scenarios import (
    MutationPolicy,
    generate_scenario_recipes,
    load_scenario_results,
    load_scenario_seeds,
    write_scenario_suite,
)


FIXTURE_ROOT = Path("tests/fixtures/fail2drive_like")


class ScenarioForgeTest(unittest.TestCase):
    def test_load_fixture_seeds(self) -> None:
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")

        self.assertEqual(len(seeds), 3)
        self.assertEqual(seeds[0].seed_id, "Base_Animals_0076")
        self.assertIn("occupied_space", seeds[0].ood_tags)

    def test_load_real_fail2drive_xml_directory_when_present(self) -> None:
        route_dir = Path("../external/fail2drive/fail2drive_split")
        if not route_dir.exists():
            self.skipTest("external Fail2Drive checkout not present")

        seeds = load_scenario_seeds(route_dir)

        self.assertGreaterEqual(len(seeds), 100)
        self.assertTrue(any(seed.scenario_class == "CustomObstacles" for seed in seeds))
        self.assertTrue(any(seed.split == "Generalization" for seed in seeds))

    def test_generate_recipes_is_deterministic(self) -> None:
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
        policy = MutationPolicy(mutations=("occlusion", "visual_noise"))

        first = generate_scenario_recipes(seeds, policy, count=4, random_seed=11)
        second = generate_scenario_recipes(seeds, policy, count=4, random_seed=11)

        self.assertEqual(
            [recipe.to_jsonable() for recipe in first],
            [recipe.to_jsonable() for recipe in second],
        )
        self.assertEqual(len(first), 4)
        self.assertIn(first[0].mutation, {"occlusion", "visual_noise"})

    def test_write_scenario_suite_artifacts(self) -> None:
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
        recipes = generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("lane_blockage",)),
            count=2,
            random_seed=3,
        )
        with TemporaryDirectory() as tmp:
            summary = write_scenario_suite(Path(tmp), seeds, recipes)

            self.assertEqual(summary["num_seeds"], 3)
            self.assertEqual(summary["num_recipes"], 2)
            self.assertTrue(Path(summary["recipes_path"]).exists())
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            self.assertIn("Generated Recipes", report)

    def test_memory_bank_and_retrieval(self) -> None:
        results = load_scenario_results(FIXTURE_ROOT / "results.json")
        bank = build_memory_bank(results)
        seeds = load_scenario_seeds(FIXTURE_ROOT / "seeds.json")
        recipe = generate_scenario_recipes(
            seeds,
            MutationPolicy(mutations=("obstacle_substitution",)),
            count=1,
            random_seed=1,
        )[0]

        matches = retrieve_memory(recipe, bank, limit=2)

        self.assertEqual(len(bank.entries), 2)
        self.assertGreaterEqual(len(matches), 1)
        self.assertIn("occupied space", matches[0].principle)

    def test_write_memory_bank_artifacts(self) -> None:
        results = load_scenario_results(FIXTURE_ROOT / "results.json")
        bank = build_memory_bank(results)
        with TemporaryDirectory() as tmp:
            summary = write_memory_bank(Path(tmp), bank)

            self.assertEqual(summary["num_entries"], 2)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(payload["entries"]), 2)


if __name__ == "__main__":
    unittest.main()
