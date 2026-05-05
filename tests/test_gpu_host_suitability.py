import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from driverx.cli import main
from driverx.simulators import (
    assess_gpu_host_suitability,
    write_gpu_host_suitability_report,
)


class GpuHostSuitabilityTest(unittest.TestCase):
    def test_h100_carla_vulkan_blocker_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            compatibility = _write_json(
                root / "torch_cuda_compatibility.json",
                {
                    "device_name": "NVIDIA H100 80GB HBM3",
                    "required_arch": "sm_90",
                    "compiled_arches": ["sm_80", "sm_86", "sm_90"],
                    "torch_version": "2.2.0+cu121",
                    "torch_cuda": "12.1",
                    "compatible": True,
                },
            )
            diagnostics = root / "carla_runtime_diagnostics.md"
            diagnostics.write_text(
                "deviceName = llvmpipe\nERROR_INCOMPATIBLE_DRIVER\nCARLA did not open port 20000 within 120s\n",
                encoding="utf-8",
            )
            evidence = _write_json(
                root / "remote_simlingo_evidence.json",
                {
                    "state": "route_infrastructure_blocked",
                    "blockers": ["CARLA server did not open port before route execution"],
                },
            )

            assessment = assess_gpu_host_suitability(
                torch_compatibility_path=compatibility,
                carla_diagnostics_path=diagnostics,
                simlingo_evidence_path=evidence,
            )

        self.assertEqual(assessment.overall_state, "blocked")
        self.assertIn("CARLA graphics runtime is blocked", assessment.blockers[0])
        self.assertIn("graphics-capable NVIDIA host", assessment.recommendation)
        self.assertEqual(assessment.checks[0].status, "ready")
        self.assertEqual(assessment.checks[1].status, "blocked")

    def test_blackwell_torch_arch_blocker_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            compatibility = _write_json(
                root / "torch_cuda_compatibility.json",
                {
                    "device_name": "NVIDIA RTX PRO 6000 Blackwell Server Edition",
                    "required_arch": "sm_120",
                    "compiled_arches": ["sm_80", "sm_86", "sm_90"],
                    "compatible": False,
                },
            )

            assessment = assess_gpu_host_suitability(torch_compatibility_path=compatibility)

        self.assertEqual(assessment.overall_state, "blocked")
        self.assertIn("sm_120", assessment.blockers[0])
        self.assertIn("rebuild", assessment.recommendation)

    def test_small_root_disk_is_warning_not_hard_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            compatibility = _write_json(
                root / "torch_cuda_compatibility.json",
                {"device_name": "A40", "required_arch": "sm_86", "compiled_arches": ["sm_86"], "compatible": True},
            )
            diagnostics = root / "carla_runtime_diagnostics.md"
            diagnostics.write_text("NVIDIA Vulkan device ready\n", encoding="utf-8")
            snapshot = root / "snapshot.txt"
            snapshot.write_text("overlay          20G   16M   20G   1% /\n", encoding="utf-8")

            summary = write_gpu_host_suitability_report(
                root / "out",
                assess_gpu_host_suitability(
                    gpu_snapshot_path=snapshot,
                    torch_compatibility_path=compatibility,
                    carla_diagnostics_path=diagnostics,
                ),
            )
            json_exists = Path(summary["json_path"]).exists()
            report_exists = Path(summary["report_path"]).exists()

        self.assertEqual(summary["overall_state"], "ready")
        self.assertIn("Root disk is only 20GB", summary["warnings"][0])
        self.assertTrue(json_exists)
        self.assertTrue(report_exists)

    def test_cli_writes_host_suitability_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            compatibility = _write_json(
                root / "torch_cuda_compatibility.json",
                {"device_name": "H100", "required_arch": "sm_90", "compiled_arches": ["sm_90"], "compatible": True},
            )
            stream = StringIO()

            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "assess-gpu-host",
                        "--torch-compatibility",
                        str(compatibility),
                        "--output-root",
                        tmp,
                        "--run-id",
                        "host-check",
                    ]
                )

            result = json.loads(stream.getvalue())
            json_exists = Path(result["json_path"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["checks"][0]["status"], "ready")
        self.assertTrue(json_exists)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
