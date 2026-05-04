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
        self.assertIn("git rev-parse --show-toplevel 2>/dev/null || pwd", script)

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

    def test_remote_gpu_sync_excludes_secrets_and_heavy_assets(self) -> None:
        script = (ROOT / "scripts" / "sync_remote_gpu.sh").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --show-toplevel 2>/dev/null || pwd", script)
        self.assertIn("--include='.env.example'", script)
        self.assertIn("--exclude='.env'", script)
        self.assertIn("--exclude='data/'", script)
        self.assertIn("--exclude='artifacts/'", script)
        self.assertIn("/usr/bin/python3 -m unittest discover -s tests", script)
        self.assertLess(
            script.index("--include='.env.example'"),
            script.index("--exclude='.env.*'"),
        )

    def test_remote_simlingo_bootstrap_handles_packaged_carla_layout(self) -> None:
        script = (ROOT / "scripts" / "remote_simlingo_bootstrap.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("ensure_carla_compat_layout", script)
        self.assertIn("Binaries/Linux/CarlaUE4-Linux-Shipping", script)
        self.assertIn("LD_LIBRARY_PATH", script)
        self.assertIn("CarlaUE4 \"$@\"", script)
        self.assertIn("prepare_runtime_user", script)
        self.assertIn("run_one_route_as_user.sh", script)
        self.assertIn('export PYTHONPATH="${SIMLINGO_ROOT}:', script)
        self.assertIn('HOME="/home/${RUNTIME_USER}"', script)
        self.assertIn("safe.directory", script)
        self.assertIn("PythonAPI/carla", script)
        self.assertIn("Engine/Content", script)
        self.assertNotIn("--strip-components=1", script)
        self.assertIn("carla-0.9.15*py3*linux-x86_64.egg", script)
        self.assertIn("CHECKPOINT_RELATIVE_PATH", script)
        self.assertIn("simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt", script)
        self.assertIn("HF_REVISION", script)
        self.assertIn("26c7c89e797d4e25bbf640013317af8da26a5454", script)
        self.assertIn("model_revision.txt", script)
        self.assertIn("checkpoint.sha256", script)
        self.assertIn("torch_cuda_compatibility.json", script)
        self.assertIn("torch.cuda.get_arch_list()", script)
        self.assertIn('token=os.environ.get("HF_TOKEN") or None', script)
        self.assertIn('DRIVERX_PYTHON="${DRIVERX_PYTHON:-/usr/bin/python3}"', script)
        self.assertNotIn("huggingface/token", script)

    def test_remote_simlingo_launcher_uses_temporary_token_file(self) -> None:
        script = (ROOT / "scripts" / "run_remote_simlingo_bootstrap.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("load_env_value HF_TOKEN", script)
        self.assertIn("REMOTE_TOKEN_FILE", script)
        self.assertIn("cleanup_remote_token_file", script)
        self.assertIn("trap cleanup_remote_token_file EXIT", script)
        self.assertIn("rm -f '${REMOTE_TOKEN_FILE}'", script)
        self.assertIn("tmux new-session", script)
        self.assertIn("remote_simlingo_bootstrap.sh", script)
        self.assertNotIn("/root/.cache/huggingface/token", script)

    def test_remote_simlingo_launcher_cleans_token_when_launch_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "ssh.log"
            count_path = tmp_path / "ssh.count"
            fake_ssh = tmp_path / "ssh"
            fake_ssh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'count_file="${FAKE_SSH_COUNT}"',
                        'count=0',
                        'if [ -f "${count_file}" ]; then count="$(cat "${count_file}")"; fi',
                        'count=$((count + 1))',
                        'printf "%s" "${count}" > "${count_file}"',
                        'printf "CALL:%s:%s\\n" "${count}" "$*" >> "${FAKE_SSH_LOG}"',
                        'if [ "${count}" = "1" ]; then cat >/dev/null; exit 0; fi',
                        'if [ "${count}" = "2" ]; then exit 42; fi',
                        'exit 0',
                    ]
                ),
                encoding="utf-8",
            )
            fake_ssh.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}:{env['PATH']}"
            env["HF_TOKEN"] = "fake-token"
            env["FAKE_SSH_LOG"] = str(log_path)
            env["FAKE_SSH_COUNT"] = str(count_path)
            result = subprocess.run(
                [
                    "bash",
                    "scripts/run_remote_simlingo_bootstrap.sh",
                    "fake-host",
                    "/workspace/0xDriver",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 42)
            log = log_path.read_text(encoding="utf-8")

        self.assertIn("CALL:1:", log)
        self.assertIn("CALL:2:", log)
        self.assertIn("CALL:3:", log)
        self.assertIn("cat > '/tmp/driverx_hf_token_task17_", log)
        self.assertIn("tmux new-session", log)
        self.assertIn("rm -f '/tmp/driverx_hf_token_task17_", log)


if __name__ == "__main__":
    unittest.main()
