import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main


class SimLingoSidecarRunnerCliTest(unittest.TestCase):
    def test_run_simlingo_sidecar_cli_writes_run_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "simlingo_sidecar_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "commands": [
                            {
                                "label": "one",
                                "command": [sys.executable, "-c", "print('hello')"],
                                "cwd": str(root),
                                "env": {},
                                "start_after_s": 0.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "run-simlingo-sidecar",
                        "--plan",
                        str(plan_path),
                        "--timeout-s",
                        "5",
                        "--output-root",
                        tmp,
                        "--run-id",
                        "sidecar-run",
                    ]
                )
            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()
            report_exists = Path(result["report_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["success"])
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)


if __name__ == "__main__":
    unittest.main()
