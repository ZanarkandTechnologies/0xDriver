from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from driverx.core.config import DatasetConfig
from driverx.core.types import CameraImage, FrameBundle
from driverx.datasets.waymo_e2e import WaymoDependencyError, load_waymo_frame


class WaymoLoaderTest(unittest.TestCase):
    def test_load_waymo_json_fixture(self) -> None:
        frame = load_waymo_frame(
            DatasetConfig(
                kind="waymo",
                name="waymo_json_fixture",
                path=Path("tests/fixtures/waymo_e2e_frame.json"),
            )
        )
        self.assertEqual(frame.frame_name, "waymo_json_fixture_001")
        self.assertEqual(len(frame.front_images), 3)
        self.assertEqual(len(frame.future_xy or []), 20)

    def test_missing_waymo_path_fails_clearly(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_waymo_frame(DatasetConfig(kind="waymo", name="missing", path=None))

    def test_tfrecord_without_optional_deps_fails_with_install_hint(self) -> None:
        with TemporaryDirectory() as tmp:
            shard = Path(tmp) / "sample.tfrecord"
            shard.write_bytes(b"")
            with patch(
                "driverx.datasets.waymo_e2e.importlib.import_module",
                side_effect=ModuleNotFoundError("tensorflow"),
            ):
                with self.assertRaises(WaymoDependencyError) as context:
                    load_waymo_frame(
                        DatasetConfig(
                            kind="waymo",
                            name="sample",
                            path=shard,
                        )
                    )
        self.assertIn("Install optional Waymo dependencies", str(context.exception))

    def test_tfrecord_glob_reaches_optional_dependency_boundary(self) -> None:
        with TemporaryDirectory() as tmp:
            shard = Path(tmp) / "validation.tfrecord-00000"
            shard.write_bytes(b"")
            glob_path = Path(tmp) / "*.tfrecord*"
            with patch(
                "driverx.datasets.waymo_e2e.importlib.import_module",
                side_effect=ModuleNotFoundError("tensorflow"),
            ):
                with self.assertRaises(WaymoDependencyError):
                    load_waymo_frame(
                        DatasetConfig(
                            kind="waymo",
                            name="sample",
                            path=glob_path,
                        )
                    )

    def test_tfrecord_frame_index_records_selected_shard_source(self) -> None:
        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.tfrecord"
            second = Path(tmp) / "b.tfrecord"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            with patch(
                "driverx.datasets.waymo_e2e._load_waymo_dependencies",
                return_value=(_FakeTf(), _FakeWaymoPb2),
            ), patch(
                "driverx.datasets.waymo_e2e._frame_from_waymo_proto",
                side_effect=_fake_frame_from_waymo_proto,
            ):
                frame = load_waymo_frame(
                    DatasetConfig(
                        kind="waymo",
                        name="multi",
                        path=Path(tmp),
                        frame_index=1,
                    )
                )
        self.assertEqual(frame.metadata["source_path"], str(second))
        self.assertEqual(frame.metadata["frame_index"], 1)


class _FakeDataset:
    def __init__(self, paths: list[str], compression_type: str) -> None:
        self.paths = paths
        self.compression_type = compression_type

    def as_numpy_iterator(self) -> object:
        for path in self.paths:
            yield path.encode("utf-8")


class _FakeTf:
    class data:
        TFRecordDataset = _FakeDataset


class _FakeWaymoFrame:
    def ParseFromString(self, raw_data: bytes) -> None:
        self.raw_data = raw_data


class _FakeWaymoPb2:
    E2EDFrame = _FakeWaymoFrame


def _fake_frame_from_waymo_proto(
    data: _FakeWaymoFrame,
    source_path: Path,
    frame_index: int,
    tf: _FakeTf,
) -> FrameBundle:
    del data, tf
    return FrameBundle(
        frame_name="fake_waymo",
        front_images=[
            CameraImage(
                name="front",
                width=1,
                height=1,
                pixels=[[(1, 2, 3)]],
            )
        ],
        ego_history_xy=[(0.0, 0.0), (1.0, 0.0)],
        future_xy=[(float(index), 0.0) for index in range(20)],
        metadata={"source_path": str(source_path), "frame_index": frame_index},
    )


if __name__ == "__main__":
    unittest.main()
