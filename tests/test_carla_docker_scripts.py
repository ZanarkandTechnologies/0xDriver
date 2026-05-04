from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CarlaDockerScriptsTest(unittest.TestCase):
    def test_carla_client_dockerfile_pins_carla_0916_default(self) -> None:
        dockerfile = (ROOT / "docker" / "carla-client.Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("ARG CARLA_PYTHON_VERSION=0.9.16", dockerfile)
        self.assertIn('"carla==${CARLA_PYTHON_VERSION}"', dockerfile)

    def test_runner_prefers_built_image_and_supports_explicit_env_file(self) -> None:
        script = (ROOT / "scripts" / "run_carla_client_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("driverx-carla-client:${CARLA_PYTHON_VERSION}", script)
        self.assertIn("DRIVERX_DOCKER_ENV_FILE", script)
        self.assertIn("python:3.10-bullseye", script)
        self.assertIn("carla==${CARLA_PYTHON_VERSION}", script)

    def test_proof_script_defaults_match_documented_artifact_contract(self) -> None:
        script = (ROOT / "scripts" / "prove_carla_0916_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('CARLA_TIMEOUT_S="${CARLA_TIMEOUT_S:-1.0}"', script)
        self.assertIn('RUN_ID="${1:-task16-proof}"', script)

    def test_proof_script_exercises_probe_and_ego_smoke(self) -> None:
        script = (ROOT / "scripts" / "prove_carla_0916_docker.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("build_carla_client_docker.sh", script)
        self.assertIn("probe-carla", script)
        self.assertIn("spawn-ego-smoke", script)

    def test_proof_script_emits_expected_docker_contract_with_fake_docker(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "docker.log"
            fake_docker = tmp_path / "docker"
            fake_docker.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "%s\\n" "$*" >> "${FAKE_DOCKER_LOG}"',
                        'if [ "${1:-}" = "image" ] && [ "${2:-}" = "inspect" ]; then exit 0; fi',
                        'if [ "${1:-}" = "build" ] || [ "${1:-}" = "run" ]; then exit 0; fi',
                        "exit 0",
                    ]
                ),
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["FAKE_DOCKER_LOG"] = str(log_path)
            env.pop("CARLA_CLIENT_DOCKER_IMAGE", None)
            env.pop("CARLA_TIMEOUT_S", None)
            env.pop("CARLA_TICK_COUNT", None)
            env.pop("DRIVERX_DOCKER_ENV_FILE", None)

            result = subprocess.run(
                ["bash", "scripts/prove_carla_0916_docker.sh"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            log = log_path.read_text(encoding="utf-8")

        self.assertIn(
            "build --platform linux/amd64 --build-arg CARLA_PYTHON_VERSION=0.9.16",
            log,
        )
        self.assertIn("image inspect driverx-carla-client:0.9.16", log)
        self.assertIn("--run-id task16-proof-probe", log)
        self.assertIn("--run-id task16-proof-ego", log)
        self.assertIn("--timeout-s 1.0", log)
        self.assertIn("--tick-count 5", log)
        self.assertNotIn("--env-file", log)


if __name__ == "__main__":
    unittest.main()
