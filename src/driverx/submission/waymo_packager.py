"""Waymo E2E submission packaging.

The default path writes a dependency-free dry-run package. Passing
``official=True`` uses the official Waymo protobuf module when installed.
"""

from __future__ import annotations

import importlib
import json
import re
import struct
from pathlib import Path
from typing import Any

from driverx.waymo_runtime import WAYMO_RUNTIME_HINT


class WaymoSubmissionDependencyError(ImportError):
    """Raised when official submission packaging is requested without Waymo deps."""


PARAMETER_COUNT_PATTERN = re.compile(r"^\d+[KMBTPE]$")


def _varint(value: int) -> bytes:
    chunks = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            chunks.append(to_write | 0x80)
        else:
            chunks.append(to_write)
            return bytes(chunks)


def _field_key(field_number: int, wire_type: int) -> bytes:
    return _varint((field_number << 3) | wire_type)


def _string_field(field_number: int, value: str) -> bytes:
    encoded = value.encode("utf-8")
    return _field_key(field_number, 2) + _varint(len(encoded)) + encoded


def _float_field(field_number: int, value: float) -> bytes:
    return _field_key(field_number, 5) + struct.pack("<f", float(value))


def _message_field(field_number: int, payload: bytes) -> bytes:
    return _field_key(field_number, 2) + _varint(len(payload)) + payload


def _trajectory_message(points_xy: list[list[float]]) -> bytes:
    payload = bytearray()
    for point in points_xy:
        payload += _float_field(1, float(point[0]))
    for point in points_xy:
        payload += _float_field(2, float(point[1]))
    return bytes(payload)


def _prediction_message(frame_name: str, points_xy: list[list[float]]) -> bytes:
    trajectory = _trajectory_message(points_xy)
    return _string_field(1, frame_name) + _message_field(2, trajectory)


def _submission_message(package: dict[str, Any]) -> bytes:
    payload = bytearray()
    for prediction in package["predictions"]:
        points_xy = [
            [x, y]
            for x, y in zip(
                prediction["trajectory"]["pos_x"],
                prediction["trajectory"]["pos_y"],
                strict=True,
            )
        ]
        payload += _message_field(
            1,
            _prediction_message(prediction["frame_name"], points_xy),
        )
    payload += _string_field(2, package["submission_type"])
    for author in package["authors"]:
        payload += _string_field(3, author)
    payload += _string_field(4, package["affiliation"])
    payload += _string_field(5, package["unique_method_name"])
    return bytes(payload)


def _load_submission_pb2() -> Any:
    try:
        return importlib.import_module(
            "waymo_open_dataset.protos.end_to_end_driving_submission_pb2"
        )
    except (ImportError, ModuleNotFoundError) as exc:
        raise WaymoSubmissionDependencyError(
            "Official Waymo submission packaging requires "
            f"waymo-open-dataset. {WAYMO_RUNTIME_HINT}"
        ) from exc


def _write_schema(run_dir: Path) -> Path:
    schema_path = run_dir / "submission_schema.proto"
    schema_path.write_text(
        '''syntax = "proto3";

message TrajectoryPrediction {
  repeated float pos_x = 1;
  repeated float pos_y = 2;
}

message FrameTrajectoryPredictions {
  string frame_name = 1;
  TrajectoryPrediction trajectory = 2;
}

message E2EDChallengeSubmissionDryRun {
  repeated FrameTrajectoryPredictions predictions = 1;
  string submission_type = 2;
  repeated string authors = 3;
  string affiliation = 4;
  string unique_method_name = 5;
}
''',
        encoding="utf-8",
    )
    return schema_path


def _public_model_names(metadata: dict[str, Any]) -> list[str]:
    raw_names = metadata.get("public_model_names")
    if isinstance(raw_names, list):
        return [str(name) for name in raw_names if str(name)]
    if isinstance(raw_names, str) and raw_names.strip():
        return [part.strip() for part in raw_names.split(",") if part.strip()]
    return ["mock-vla-intent-reasoner"]


def _build_package(run_dir: Path) -> dict[str, Any]:
    trajectory_path = run_dir / "selected_trajectory.json"
    frame_path = run_dir / "frame.json"
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Missing selected trajectory: {trajectory_path}")
    if not frame_path.exists():
        raise FileNotFoundError(f"Missing frame artifact: {frame_path}")

    trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    metadata_path = run_dir / "run_metadata.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    package = {
        "submission_type": "E2ED_SUBMISSION_DRY_RUN",
        "authors": [str(metadata.get("author", "0xDriver"))],
        "affiliation": str(metadata.get("affiliation", "Independent")),
        "account_name": str(metadata.get("account_name", "")),
        "unique_method_name": str(
            metadata.get("method_name", "fixture_vla_intent_planner")
        ),
        "method_link": str(metadata.get("method_link", "")),
        "description": str(metadata.get("description", "")),
        "uses_public_model_pretraining": True,
        "public_model_names": _public_model_names(metadata),
        "num_model_parameters": str(metadata.get("num_model_parameters", "0K")),
        "predictions": [
            {
                "frame_name": frame["frame_name"],
                "trajectory": {
                    "pos_x": [point[0] for point in trajectory["points_xy"]],
                    "pos_y": [point[1] for point in trajectory["points_xy"]],
                },
            }
        ],
    }
    return package


def _validate_official_package(package: dict[str, Any]) -> None:
    if not package["account_name"] or "@" not in package["account_name"]:
        raise ValueError(
            "Official Waymo submission requires account_name to be the email "
            "used to register at waymo.com/open."
        )
    if not package["unique_method_name"]:
        raise ValueError("Official Waymo submission requires unique_method_name.")
    if not package["authors"] or not all(package["authors"]):
        raise ValueError("Official Waymo submission requires at least one author.")
    if not PARAMETER_COUNT_PATTERN.fullmatch(package["num_model_parameters"]):
        raise ValueError(
            "Official Waymo submission requires num_model_parameters as an "
            "integer plus suffix, for example '200K', '7B', or '0K'."
        )
    if package["uses_public_model_pretraining"] and not package["public_model_names"]:
        raise ValueError(
            "Official Waymo submission requires public_model_names when "
            "uses_public_model_pretraining is true."
        )
    for prediction in package["predictions"]:
        pos_x = prediction["trajectory"]["pos_x"]
        pos_y = prediction["trajectory"]["pos_y"]
        if len(pos_x) != 20 or len(pos_y) != 20:
            raise ValueError(
                "Official Waymo submission trajectories must contain exactly "
                "20 x/y waypoints."
            )


def _write_dry_run_package(
    run_dir: Path, package: dict[str, Any], output_path: Path | None
) -> dict[str, Any]:
    output = output_path or (run_dir / "submission_dry_run.json")
    output.write_text(json.dumps(package, indent=2), encoding="utf-8")
    shard_path = run_dir / "submission_shard_00000.pb"
    shard_path.write_bytes(_submission_message(package))
    schema_path = _write_schema(run_dir)
    return {
        "path": str(output),
        "protobuf_shard": str(shard_path),
        "protobuf_schema": str(schema_path),
        "official": False,
        "predictions": len(package["predictions"]),
    }


def _write_official_package(
    run_dir: Path, package: dict[str, Any], output_path: Path | None
) -> dict[str, Any]:
    submission_pb2 = _load_submission_pb2()
    _validate_official_package(package)
    predictions = []
    for prediction in package["predictions"]:
        trajectory = submission_pb2.TrajectoryPrediction(
            pos_x=prediction["trajectory"]["pos_x"],
            pos_y=prediction["trajectory"]["pos_y"],
        )
        predictions.append(
            submission_pb2.FrameTrajectoryPredictions(
                frame_name=prediction["frame_name"],
                trajectory=trajectory,
            )
        )

    submission = submission_pb2.E2EDChallengeSubmission(predictions=predictions)
    submission.submission_type = (
        submission_pb2.E2EDChallengeSubmission.SubmissionType.E2ED_SUBMISSION
    )
    submission.authors[:] = package["authors"]
    submission.affiliation = package["affiliation"]
    submission.account_name = package["account_name"]
    submission.unique_method_name = package["unique_method_name"]
    submission.method_link = package["method_link"]
    submission.description = package["description"]
    submission.uses_public_model_pretraining = package["uses_public_model_pretraining"]
    submission.public_model_names.extend(package["public_model_names"])
    submission.num_model_parameters = package["num_model_parameters"]

    output = output_path or (run_dir / "submission_official_shard_00000.pb")
    output.write_bytes(submission.SerializeToString())
    return {
        "path": str(output),
        "protobuf_shard": str(output),
        "protobuf_schema": "official_waymo_open_dataset",
        "official": True,
        "predictions": len(package["predictions"]),
    }


def package_run_dir(
    run_dir: Path,
    output_path: Path | None = None,
    official: bool = False,
) -> dict[str, Any]:
    package = _build_package(run_dir)
    if not official:
        return _write_dry_run_package(run_dir, package, output_path)
    dry_run_result = _write_dry_run_package(run_dir, package, None)
    official_result = _write_official_package(run_dir, package, output_path)
    return {
        **official_result,
        "dry_run_json": dry_run_result["path"],
    }
