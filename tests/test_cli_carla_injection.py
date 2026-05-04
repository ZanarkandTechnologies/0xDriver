import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.cli import main
from driverx.simulators import OverlayInjectionRunResult, OverlayRouteInjectionResult


class CarlaInjectionCliTest(unittest.TestCase):
    def test_run_overlay_injection_cli_writes_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "carla.json"
            plan_path = root / "overlay_injection_plan.json"
            config_path.write_text(
                json.dumps(
                    {
                        "carla": {"host": "127.0.0.1", "port": 2000, "timeout_s": 0.5},
                        "fail2drive": {"root": str(root), "route_path": "route.xml", "agent_path": "agent.py"},
                    }
                ),
                encoding="utf-8",
            )
            plan_path.write_text('{"routes": []}', encoding="utf-8")
            route_result = OverlayRouteInjectionResult(
                route_index=0,
                recipe_id="route-occlusion",
                companion_actor_refs=["companion_actor_0"],
                spawned_actor_ids=[101],
                destroyed_actor_ids=[101],
                applied_tick_count=1,
                track_count=1,
            )
            fake_result = OverlayInjectionRunResult(
                connected=True,
                host="127.0.0.1",
                port=2000,
                plan_path=str(plan_path),
                route_count=1,
                route_results=[route_result],
                spawned_actor_ids=[101],
                destroyed_actor_ids=[101],
                track_count=1,
            )
            stream = StringIO()
            with patch(
                "driverx.simulators.run_overlay_injection_plan",
                return_value=fake_result,
            ) as run_overlay, redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-overlay-injection",
                        "--config",
                        str(config_path),
                        "--plan",
                        str(plan_path),
                        "--route-limit",
                        "1",
                        "--tick-limit",
                        "2",
                        "--no-wait-for-tick",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "inject-run",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["connected"])
        self.assertEqual(result["route_results"][0]["recipe_id"], "route-occlusion")
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)
        config_arg = run_overlay.call_args.args[0]
        self.assertEqual(config_arg.route_limit, 1)
        self.assertEqual(config_arg.tick_limit, 2)
        self.assertFalse(config_arg.wait_for_tick)


if __name__ == "__main__":
    unittest.main()
