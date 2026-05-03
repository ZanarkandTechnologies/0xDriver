from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.core.types import CameraImage, FrameBundle
from driverx.core.config import DatasetConfig, DriverConfig, OutputConfig, ReasonerConfig
from driverx.pipeline.batch_run import DEFAULT_WAYMO_BATCH_COUNT, run_batch


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

    def test_fixture_config_defaults_to_standard_batch(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(kind="fixture", name="construction_merge"),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="batch-default"),
            )
            summary = run_batch(config)
        self.assertEqual(summary["num_scenes"], 2)
        self.assertEqual(
            [scene["fixture"] for scene in summary["scenes"]],
            ["construction_merge", "straight_clear"],
        )

    def test_run_batch_over_fake_waymo_frames_writes_report(self) -> None:
        with TemporaryDirectory() as tmp:
            config = DriverConfig(
                dataset=DatasetConfig(
                    kind="waymo",
                    name="fake_waymo",
                    path=Path("unused.tfrecord"),
                ),
                reasoner=ReasonerConfig(backend="mock", uncertainty=0.34),
                output=OutputConfig(root=Path(tmp), run_id="waymo-batch"),
            )
            frames = [_fake_frame("waymo_001", 0.0), _fake_frame("waymo_002", 24.0)]
            with patch(
                "driverx.pipeline.batch_run.iter_waymo_frames",
                return_value=iter(frames),
            ):
                summary = run_batch(config, frame_start=3, frame_count=2)

            summary_path = Path(summary["summary_path"])
            report_path = Path(summary["report_path"])
            self.assertEqual(summary["dataset_kind"], "waymo")
            self.assertEqual(summary["frame_start"], 3)
            self.assertEqual(summary["frame_count"], 2)
            self.assertEqual(summary["num_scenes"], 2)
            self.assertIsNotNone(summary["mean_ade"])
            self.assertEqual(
                summary["scenes"][0]["selected_source"],
                "constant_acceleration_smooth",
            )
            self.assertIn("load_frame", summary["mean_timings_ms"])
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(Path(summary["worst_scene"]["scene_prediction"]).exists())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("## ADE Table", report)
            self.assertIn("## Latency Table", report)
            self.assertIn("Worst-scene SVG", report)

    def test_waymo_batch_defaults_to_ten_frames_without_count(self) -> None:
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
            frames = [
                _fake_frame(f"waymo_{index:03d}", float(index))
                for index in range(DEFAULT_WAYMO_BATCH_COUNT)
            ]
            with patch(
                "driverx.pipeline.batch_run.iter_waymo_frames",
                return_value=iter(frames),
            ) as iterator:
                summary = run_batch(config)

        self.assertEqual(summary["frame_count"], DEFAULT_WAYMO_BATCH_COUNT)
        self.assertEqual(summary["num_scenes"], DEFAULT_WAYMO_BATCH_COUNT)
        iterator.assert_called_once_with(
            config.dataset,
            start_index=0,
            count=DEFAULT_WAYMO_BATCH_COUNT,
        )


def _image() -> CameraImage:
    return CameraImage(name="front", width=1, height=1, pixels=[[(10, 20, 30)]])


def _fake_frame(name: str, lateral_offset: float) -> FrameBundle:
    return FrameBundle(
        frame_name=name,
        front_images=[_image()],
        ego_history_xy=[(0.0, 0.0), (1.0, 0.0)],
        future_xy=[(float(index + 2), lateral_offset) for index in range(20)],
        metadata={"dataset": "waymo_e2e", "scenario": "unknown", "hazards": []},
    )


if __name__ == "__main__":
    unittest.main()
