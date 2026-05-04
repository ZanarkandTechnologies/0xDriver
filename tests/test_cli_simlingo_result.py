import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main


class SimLingoResultCliTest(unittest.TestCase):
    def test_ingest_simlingo_result_cli_writes_compact_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = root / "seed_1_res.json"
            result_path.write_text(
                json.dumps(
                    {
                        "_checkpoint": {
                            "global_record": {
                                "status": "Failed",
                                "scores_mean": {
                                    "score_route": 0,
                                    "score_penalty": 1.0,
                                    "score_composed": 0.0,
                                },
                                "meta": {
                                    "exceptions": [["route-1", 0, "Failed - Agent crashed"]]
                                },
                            },
                            "progress": [1, 1],
                            "records": [
                                {
                                    "route_id": "route-1",
                                    "scenario_name": "ParkingCutIn_1",
                                    "town_name": "Town12",
                                    "status": "Failed - Agent crashed",
                                    "scores": {
                                        "score_route": 0,
                                        "score_penalty": 1.0,
                                        "score_composed": 0.0,
                                    },
                                    "infractions": {"route_timeout": []},
                                    "meta": {},
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "ingest-simlingo-result",
                        "--result",
                        str(result_path),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "simlingo-result",
                    ]
                )
            result = json.loads(stream.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertFalse(result["record"]["success"])
            self.assertEqual(result["primary_route"]["route_id"], "route-1")
            self.assertTrue(Path(result["json_path"]).exists())
            self.assertTrue(Path(result["report_path"]).exists())
            self.assertNotIn("route_log", result)
            self.assertNotIn("tail", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
