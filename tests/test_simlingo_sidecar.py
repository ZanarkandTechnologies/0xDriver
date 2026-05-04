import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators import build_simlingo_sidecar_plan, write_simlingo_sidecar_plan


def _write_simlingo_plan(path: Path, blockers: list[str] | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "command": ["python", "leaderboard_evaluator.py", "--routes=routes.xml"],
                "cwd": str(path.parent / "simlingo"),
                "env": {"PYTHONPATH": "simlingo-path", "SAVE_PATH": "viz"},
                "expected_outputs": [str(path.parent / "out" / "seed_1_res.json")],
                "live_blockers": blockers or [],
            }
        ),
        encoding="utf-8",
    )


def _write_overlay_plan(path: Path, errors: list[str] | None = None, route_count: int = 2) -> None:
    path.write_text(
        json.dumps(
            {
                "num_routes": route_count,
                "validation_errors": errors or [],
                "routes": [{"recipe_id": f"route-{index}"} for index in range(route_count)],
            }
        ),
        encoding="utf-8",
    )


class SimLingoSidecarTest(unittest.TestCase):
    def test_build_simlingo_sidecar_plan_pairs_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            simlingo_plan = tmp_path / "simlingo_command_plan.json"
            overlay_plan = tmp_path / "overlay_injection_plan.json"
            _write_simlingo_plan(simlingo_plan)
            _write_overlay_plan(overlay_plan)

            plan = build_simlingo_sidecar_plan(
                simlingo_plan_path=simlingo_plan,
                overlay_plan_path=overlay_plan,
                output_dir=tmp_path / "run",
                carla_config_path=Path("configs/carla_local.sample.yaml"),
                tick_limit=3,
                overlay_start_delay_s=7.5,
                use_docker_carla_client=True,
            )
            summary = write_simlingo_sidecar_plan(tmp_path / "run", plan)
            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertTrue(plan.dry_run)
        self.assertEqual(plan.launch_mode, "manual_two_process_sidecar")
        self.assertEqual(plan.route_count, 2)
        self.assertEqual([command.label for command in plan.commands], [
            "simlingo_bench2drive",
            "driverx_overlay_injector",
        ])
        self.assertEqual(plan.commands[1].start_after_s, 7.5)
        self.assertEqual(plan.commands[1].command[:3], ["bash", "scripts/run_carla_client_docker.sh", "python"])
        self.assertNotIn("--route-limit", plan.commands[1].command)
        self.assertIn("--tick-limit", plan.commands[1].command)
        self.assertEqual(plan.commands[0].env["SAVE_PATH"], "viz")
        self.assertEqual(payload["blockers"], [])
        self.assertIn("SimLingo Sidecar Plan", report)

    def test_build_simlingo_sidecar_plan_surfaces_input_blockers(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            simlingo_plan = tmp_path / "simlingo_command_plan.json"
            overlay_plan = tmp_path / "overlay_injection_plan.json"
            _write_simlingo_plan(simlingo_plan, blockers=["needs H100"])
            _write_overlay_plan(overlay_plan, errors=["bad overlay"], route_count=0)

            plan = build_simlingo_sidecar_plan(
                simlingo_plan_path=simlingo_plan,
                overlay_plan_path=overlay_plan,
                output_dir=tmp_path / "run",
                carla_config_path=Path("configs/carla_local.sample.yaml"),
            )

        self.assertIn("needs H100", plan.blockers)
        self.assertIn("Overlay plan validation error: bad overlay", plan.blockers)
        self.assertIn("Overlay plan contains no routes.", plan.blockers)

    def test_build_simlingo_sidecar_plan_flags_missing_simlingo_command(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            simlingo_plan = tmp_path / "simlingo_command_plan.json"
            overlay_plan = tmp_path / "overlay_injection_plan.json"
            simlingo_plan.write_text('{"command": [], "cwd": ".", "env": {}}', encoding="utf-8")
            _write_overlay_plan(overlay_plan)

            plan = build_simlingo_sidecar_plan(
                simlingo_plan_path=simlingo_plan,
                overlay_plan_path=overlay_plan,
                output_dir=tmp_path / "run",
                carla_config_path=Path("configs/carla_local.sample.yaml"),
            )

        self.assertIn("SimLingo plan contains no command.", plan.blockers)


if __name__ == "__main__":
    unittest.main()
