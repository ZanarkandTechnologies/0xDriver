from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.batch_run import run_batch


class BatchTest(unittest.TestCase):
    def test_run_batch_over_fixtures(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(kind="fixture", name="construction_merge"),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="batch"),
            )
            summary = run_batch(config, ["construction_merge", "straight_clear"])
            self.assertEqual(summary["num_scenes"], 2)
            self.assertIsNotNone(summary["mean_ade"])
            self.assertTrue((Path(tmp) / "batch" / "batch_summary.json").exists())
            clear_svg = Path(tmp) / "batch" / "straight_clear" / "scene_prediction.svg"
            self.assertNotIn("service vehicle", clear_svg.read_text())


if __name__ == "__main__":
    unittest.main()
