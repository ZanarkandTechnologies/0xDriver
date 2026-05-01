"""Dry-run Waymo E2E submission packaging.

This writes a JSON artifact with the same essential frame/trajectory structure
as the official protobuf submission. Real protobuf serialization can be added
once the Waymo dependency is enabled.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any


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


def package_run_dir(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
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
        "affiliation": "Independent",
        "unique_method_name": str(
            metadata.get("method_name", "fixture_vla_intent_planner")
        ),
        "uses_public_model_pretraining": True,
        "public_model_names": ["mock-vla-intent-reasoner"],
        "num_model_parameters": "0",
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
    output = output_path or (run_dir / "submission_dry_run.json")
    output.write_text(json.dumps(package, indent=2), encoding="utf-8")
    shard_path = run_dir / "submission_shard_00000.pb"
    shard_path.write_bytes(_submission_message(package))
    schema_path = _write_schema(run_dir)
    return {
        "path": str(output),
        "protobuf_shard": str(shard_path),
        "protobuf_schema": str(schema_path),
        "predictions": len(package["predictions"]),
    }
