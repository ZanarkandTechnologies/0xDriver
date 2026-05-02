from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.core.types import CameraImage, FrameBundle
from driverx.pipeline.experiment_run import run_experiment


class ExperimentTest(unittest.TestCase):
    def test_fixture_experiment_writes_comparison_report(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(kind="fixture", name="construction_merge"),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="fixture-experiment"),
            )
            summary = run_experiment(config)

            self.assertEqual(summary["dataset_kind"], "fixture")
            self.assertEqual(summary["num_scenes"], 1)
            self.assertIn("intent_planner", summary["strategy_summaries"])
            self.assertIn("constant_velocity", summary["strategy_summaries"])
            self.assertIn("oracle_best_rule", summary["strategy_summaries"])
            self.assertTrue(Path(summary["summary_path"]).exists())
            report = Path(summary["report_path"]).read_text(encoding="utf-8")
            self.assertIn("## Strategy Mean ADE", report)
            self.assertIn("oracle_best_rule", report)
            self.assertIn("analysis-only", report)

    def test_fake_waymo_experiment_aggregates_two_frames(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(
                    kind="waymo",
                    name="fake_waymo",
                    path=Path("unused.tfrecord"),
                ),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="waymo-experiment"),
            )
            frames = [_fake_frame("waymo_001", 0.0), _fake_frame("waymo_002", 18.0)]
            with patch(
                "driverx.pipeline.experiment_run.iter_waymo_frames",
                return_value=iter(frames),
            ):
                summary = run_experiment(config, frame_start=5, frame_count=2)

            self.assertEqual(summary["frame_start"], 5)
            self.assertEqual(summary["frame_count"], 2)
            self.assertEqual(summary["num_scenes"], 2)
            self.assertEqual([frame["frame_index"] for frame in summary["frames"]], [5, 6])
            self.assertIsNotNone(summary["best_strategy_by_mean_ade"])
            self.assertEqual(summary["best_analysis_strategy_by_mean_ade"], "oracle_best_rule")
            first_frame = summary["frames"][0]
            self.assertIn("rule_ranked", first_frame["strategies"])
            self.assertTrue(
                Path(first_frame["strategies"]["constant_velocity"]["trajectory_path"]).exists()
            )

    def test_waymo_experiment_defaults_to_ten_frames(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(
                    kind="waymo",
                    name="fake_waymo",
                    path=Path("unused.tfrecord"),
                ),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="waymo-default"),
            )
            frames = [_fake_frame(f"waymo_{index:03d}", 0.0) for index in range(10)]
            with patch(
                "driverx.pipeline.experiment_run.iter_waymo_frames",
                return_value=iter(frames),
            ) as iterator:
                summary = run_experiment(config)

        self.assertEqual(summary["frame_count"], 10)
        self.assertEqual(summary["num_scenes"], 10)
        iterator.assert_called_once_with(config.dataset, 0, 10)


def _image() -> CameraImage:
    return CameraImage(name="front", width=1, height=1, pixels=[[(10, 20, 30)]])


def _fake_frame(name: str, lateral_offset: float) -> FrameBundle:
    return FrameBundle(
        frame_name=name,
        front_images=[_image()],
        ego_history_xy=[(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)],
        future_xy=[(float(index + 3), lateral_offset) for index in range(20)],
        metadata={"dataset": "waymo_e2e", "scenario": "unknown", "hazards": []},
    )


if __name__ == "__main__":
    unittest.main()
