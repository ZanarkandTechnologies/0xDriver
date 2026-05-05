import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators import OverlayEvidenceInputs, build_overlay_evidence


def _write_overlay_plan(path: Path) -> None:
    routes = [
        _route("route-cut-in", "no_signal_cut_in"),
        _route("route-brake", "sudden_brake"),
        _route("route-moto", "motorcycle_filtering"),
    ]
    path.write_text(
        json.dumps(
            {
                "route_pack_path": str(path.parent / "bench2drive_route_pack.json"),
                "route_suite_path": str(path.parent / "generated_routes.xml"),
                "routes": routes,
            }
        ),
        encoding="utf-8",
    )


def _route(recipe_id: str, behavior_id: str) -> dict:
    return {
        "recipe_id": recipe_id,
        "behavior_id": behavior_id,
        "mutation": "regional_driving_behavior",
        "expected_failure_mode": "behavior pressure",
        "route_path": f"{recipe_id}.xml",
        "overlay_path": f"{recipe_id}.json",
        "script_plan": {"ticks": [{"actor_ref": "ood_actor_0", "t_s": 0.0}]},
    }


def _write_overlay_run(path: Path, tracks_path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "connected": True,
                "host": "127.0.0.1",
                "port": 2000,
                "plan_path": str(path.parent / "overlay_injection_plan.json"),
                "route_count": 3,
                "route_results": [
                    _route_result("route-cut-in", 101),
                    _route_result("route-brake", 102),
                    _route_result("route-moto", 103),
                ],
                "spawned_actor_ids": [101, 102, 103],
                "destroyed_actor_ids": [101, 102, 103],
                "tracks_path": str(tracks_path),
                "track_count": 3,
            }
        ),
        encoding="utf-8",
    )


def _route_result(recipe_id: str, actor_id: int) -> dict:
    return {
        "route_index": actor_id - 101,
        "recipe_id": recipe_id,
        "companion_actor_refs": ["companion_actor_0"],
        "spawned_actor_ids": [actor_id],
        "destroyed_actor_ids": [actor_id],
        "applied_tick_count": 1,
        "track_count": 1,
        "error": None,
    }


def _write_tracks(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "recipe_id": "route-cut-in",
                    "actor_ref": "companion_actor_0",
                    "actor_id": 101,
                    "tick_index": 0,
                    "location": {"x": 1.0, "y": 2.0, "z": 0.2},
                },
                {
                    "recipe_id": "route-brake",
                    "actor_ref": "companion_actor_0",
                    "actor_id": 102,
                    "tick_index": 0,
                    "location": {"x": 2.0, "y": 2.0, "z": 0.2},
                },
                {
                    "recipe_id": "route-moto",
                    "actor_ref": "companion_actor_0",
                    "actor_id": 103,
                    "tick_index": 0,
                    "location": {"x": 3.0, "y": 2.0, "z": 0.2},
                },
            ]
        ),
        encoding="utf-8",
    )


class OverlayEvidenceTest(unittest.TestCase):
    def test_build_overlay_evidence_links_recipes_behavior_assertions_and_cleanup(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan = tmp_path / "overlay_injection_plan.json"
            run = tmp_path / "overlay_injection_run.json"
            tracks = tmp_path / "entity_tracks.json"
            _write_overlay_plan(plan)
            _write_tracks(tracks)
            _write_overlay_run(run, tracks)

            summary = build_overlay_evidence(
                tmp_path / "evidence",
                OverlayEvidenceInputs(overlay_plan_path=plan, overlay_run_path=run),
            )
            report = Path(summary["report_path"]).read_text(encoding="utf-8")

        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["recipe_ids"], ["route-cut-in", "route-brake", "route-moto"])
        self.assertTrue(all(assertion["passed"] for assertion in summary["behavior_assertions"]))
        self.assertEqual(summary["track_summary"]["track_count"], 3)
        self.assertEqual(summary["cleanup"]["undestroyed_actor_ids"], [])
        self.assertTrue(summary["cleanup"]["all_destroyed"])
        self.assertEqual(summary["blockers"], [])
        self.assertIn("Overlay Evidence", report)

    def test_build_overlay_evidence_missing_live_run_is_clean_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan = tmp_path / "overlay_injection_plan.json"
            _write_overlay_plan(plan)

            summary = build_overlay_evidence(
                tmp_path / "evidence",
                OverlayEvidenceInputs(overlay_plan_path=plan),
            )

        self.assertEqual(summary["status"], "blocked")
        self.assertIn("Missing live overlay run path", "\n".join(summary["blockers"]))
        self.assertTrue(all(assertion["passed"] for assertion in summary["behavior_assertions"]))

    def test_build_overlay_evidence_cli_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan = tmp_path / "overlay_injection_plan.json"
            run = tmp_path / "overlay_injection_run.json"
            tracks = tmp_path / "entity_tracks.json"
            _write_overlay_plan(plan)
            _write_tracks(tracks)
            _write_overlay_run(run, tracks)
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "build-overlay-evidence",
                        "--overlay-plan",
                        str(plan),
                        "--overlay-run",
                        str(run),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "overlay-evidence",
                    ]
                )
            summary = json.loads(stream.getvalue())
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "ready")
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
