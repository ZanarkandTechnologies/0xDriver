import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.simulators import (
    run_simlingo_sidecar_processes,
    write_simlingo_sidecar_run,
)


def _write_sidecar_plan(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "commands": [
                    {
                        "label": "simlingo_bench2drive",
                        "command": [
                            sys.executable,
                            "-c",
                            "print('simlingo ok')",
                        ],
                        "cwd": str(path.parent),
                        "env": {},
                        "start_after_s": 0.0,
                    },
                    {
                        "label": "driverx_overlay_injector",
                        "command": [
                            sys.executable,
                            "-c",
                            "print('overlay ok')",
                        ],
                        "cwd": str(path.parent),
                        "env": {},
                        "start_after_s": 0.05,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


class SimLingoSidecarRunnerTest(unittest.TestCase):
    def test_run_simlingo_sidecar_processes_executes_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "simlingo_sidecar_plan.json"
            _write_sidecar_plan(plan_path)

            result = run_simlingo_sidecar_processes(
                plan_path,
                root / "run",
                timeout_s=5.0,
            )
            summary = write_simlingo_sidecar_run(root / "run", result)

            payload = json.loads(Path(summary["json_path"]).read_text(encoding="utf-8"))
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            stdout_texts = [
                Path(record["stdout_path"]).read_text(encoding="utf-8").strip()
                for record in payload["process_records"]
            ]

        self.assertTrue(result.success)
        self.assertEqual([record.exit_code for record in result.process_records], [0, 0])
        self.assertIn("simlingo ok", stdout_texts)
        self.assertIn("overlay ok", stdout_texts)
        self.assertIn("SimLingo Sidecar Run", report)

    def test_run_simlingo_sidecar_processes_dry_run_does_not_execute(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "simlingo_sidecar_plan.json"
            _write_sidecar_plan(plan_path)

            result = run_simlingo_sidecar_processes(
                plan_path,
                root / "run",
                dry_run=True,
            )

        self.assertTrue(result.success)
        self.assertEqual([record.pid for record in result.process_records], [None, None])
        self.assertEqual([record.exit_code for record in result.process_records], [None, None])

    def test_run_simlingo_sidecar_processes_reports_bad_cwd(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "simlingo_sidecar_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "label": "missing",
                                "command": [sys.executable, "-c", "print('never')"],
                                "cwd": str(root / "missing"),
                                "env": {},
                                "start_after_s": 0.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_simlingo_sidecar_processes(plan_path, root / "run")

        self.assertFalse(result.success)
        self.assertIn("does not exist", result.process_records[0].error or "")


if __name__ == "__main__":
    unittest.main()
