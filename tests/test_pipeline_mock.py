import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.evaluation.reports import evaluate_run_dir
from driverx.pipeline.scene_run import inspect_scene, run_scene
from driverx.submission.waymo_packager import package_run_dir


class PipelineMockTest(unittest.TestCase):
    def _config(self, output_root: Path, run_id: str) -> DriverConfig:
        return DriverConfig(
            dataset=DatasetConfig(kind="fixture", name="construction_merge"),
            reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
            output=OutputConfig(root=output_root, run_id=run_id),
        )

    def test_inspect_scene_writes_svg(self) -> None:
        with TemporaryDirectory() as tmp:
            result = inspect_scene(self._config(Path(tmp), "inspect"))
            artifact_names = {artifact.name for artifact in result.artifacts}
            self.assertIn("scene_inspection", artifact_names)
            self.assertTrue((Path(tmp) / "inspect" / "scene_inspection.svg").exists())

    def test_run_scene_evaluate_and_package(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_scene(self._config(Path(tmp), "run"))
            self.assertEqual(result.frame_name, "fixture_construction_merge_001")
            self.assertIsNotNone(result.intent)
            self.assertIsNotNone(result.selected_trajectory)
            self.assertIn("ade", result.metrics)
            run_dir = Path(tmp) / "run"
            self.assertTrue((run_dir / "scene_prediction.svg").exists())
            self.assertTrue((run_dir / "raw_candidates.json").exists())
            self.assertTrue((run_dir / "smoothed_candidates.json").exists())
            self.assertTrue((run_dir / "submission_dry_run.json").exists())
            self.assertIn("generate_candidates", result.timings_ms)
            self.assertIn("smooth_candidates", result.timings_ms)
            self.assertIn("rank_candidates", result.timings_ms)

            report = evaluate_run_dir(run_dir)
            self.assertEqual(report["num_points"], 20)
            self.assertIsNotNone(report["ade"])

            package = package_run_dir(run_dir)
            self.assertEqual(package["predictions"], 1)
            submission = json.loads((run_dir / "submission_dry_run.json").read_text())
            self.assertEqual(submission["authors"], ["0xDriver"])
            self.assertEqual(submission["unique_method_name"], "fixture_vla_intent_planner")

    def test_run_scene_does_not_clobber_existing_run_id(self) -> None:
        with TemporaryDirectory() as tmp:
            config = self._config(Path(tmp), "same-id")
            first = run_scene(config)
            second = run_scene(config)
            self.assertNotEqual(first.run_dir, second.run_dir)
            self.assertTrue(first.run_dir.exists())
            self.assertTrue(second.run_dir.exists())


if __name__ == "__main__":
    unittest.main()
