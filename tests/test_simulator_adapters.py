import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.scenarios import MutationPolicy, generate_scenario_recipes, load_scenario_seeds
from driverx.simulators import (
    CarlaRunConfig,
    load_carla_run_config,
    plan_fail2drive_run,
    smoke_carla_server,
)


def _fake_fail2drive_root(root: Path) -> None:
    (root / "leaderboard" / "leaderboard").mkdir(parents=True)
    (root / "leaderboard" / "leaderboard" / "leaderboard_evaluator_local.py").write_text(
        "# fake evaluator\n",
        encoding="utf-8",
    )
    (root / "team_code").mkdir()
    (root / "team_code" / "visu_agent.py").write_text("# fake agent\n", encoding="utf-8")
    (root / "fail2drive_split").mkdir()
    for route_name in (
        "Base_Animals_0076.xml",
        "Generalization_CustomObstacles_1028.xml",
        "Generalization_PedestriansOnRoad_1088.xml",
    ):
        (root / "fail2drive_split" / route_name).write_text("<routes />\n", encoding="utf-8")


def _fake_config(root: Path, output_dir: Path) -> CarlaRunConfig:
    return CarlaRunConfig(
        host="127.0.0.1",
        port=2000,
        timeout_s=0.01,
        carla_root=None,
        fail2drive_root=root,
        route_path=Path("fail2drive_split/Generalization_PedestriansOnRoad_1088.xml"),
        agent_path=Path("team_code/visu_agent.py"),
        output_dir=output_dir,
    )


class SimulatorAdapterTest(unittest.TestCase):
    def test_plan_fail2drive_run_uses_dry_run_command_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail2drive"
            _fake_fail2drive_root(root)
            config = _fake_config(root, Path(tmp) / "outputs")
            seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
            recipe = generate_scenario_recipes(
                seeds,
                MutationPolicy(mutations=("occlusion",)),
                count=1,
                random_seed=5,
            )[0]

            plan = plan_fail2drive_run(config, recipe)

        self.assertTrue(plan.dry_run)
        self.assertEqual(plan.cwd, root.resolve())
        self.assertIn("leaderboard_evaluator_local.py", " ".join(plan.command))
        self.assertIn("--routes", plan.command)
        self.assertEqual(plan.env["CARLA_HOST"], "127.0.0.1")
        self.assertIn(str((root / recipe.route_path).resolve()), plan.command)

    def test_carla_smoke_unreachable_is_clean_result(self) -> None:
        result = smoke_carla_server("127.0.0.1", 9, 0.01)

        self.assertFalse(result.reachable)
        self.assertIsNotNone(result.error)

    def test_plan_json_is_serializable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail2drive"
            _fake_fail2drive_root(root)
            config = _fake_config(root, Path(tmp) / "outputs")
            seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
            recipe = generate_scenario_recipes(
                seeds,
                MutationPolicy(mutations=("visual_noise",)),
                count=1,
                random_seed=8,
            )[0]
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(plan_fail2drive_run(config, recipe).to_jsonable()))
            self.assertIn("expected_outputs", json.loads(path.read_text()))

    def test_plan_fail2drive_run_requires_recipe_route(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail2drive"
            _fake_fail2drive_root(root)
            config = _fake_config(root, Path(tmp) / "outputs")
            seeds = load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json"))
            recipe = generate_scenario_recipes(
                seeds,
                MutationPolicy(mutations=("occlusion",)),
                count=1,
                random_seed=5,
            )[0]
            route_less_recipe = type(recipe)(
                recipe_id=recipe.recipe_id,
                parent_seed_id=recipe.parent_seed_id,
                mutation=recipe.mutation,
                actors=recipe.actors,
                environment=recipe.environment,
                expected_failure_mode=recipe.expected_failure_mode,
                memory_query=recipe.memory_query,
                route_path=None,
            )

            with self.assertRaisesRegex(ValueError, "route_path is required"):
                plan_fail2drive_run(config, route_less_recipe)

    def test_plan_fail2drive_run_validates_external_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail2drive"
            _fake_fail2drive_root(root)
            (root / "team_code" / "visu_agent.py").unlink()
            config = _fake_config(root, Path(tmp) / "outputs")
            recipe = generate_scenario_recipes(
                load_scenario_seeds(Path("tests/fixtures/fail2drive_like/seeds.json")),
                MutationPolicy(mutations=("occlusion",)),
                count=1,
                random_seed=5,
            )[0]

            with self.assertRaisesRegex(FileNotFoundError, "Fail2Drive agent not found"):
                plan_fail2drive_run(config, recipe)


if __name__ == "__main__":
    unittest.main()
