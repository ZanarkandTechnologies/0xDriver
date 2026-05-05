#!/usr/bin/env bash
set -euo pipefail
mkdir -p "/workspace/artifacts/task20/carla"
if [ -f "/workspace/artifacts/task20/carla/carla.pid" ] && kill -0 "$(cat "/workspace/artifacts/task20/carla/carla.pid")" 2>/dev/null; then
  echo "CARLA already running with pid $(cat "/workspace/artifacts/task20/carla/carla.pid")"
  exit 0
fi
export SDL_VIDEODRIVER=offscreen
export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-}"
nohup "/workspace/software/carla0915/CarlaUE4.sh" -RenderOffScreen -nosound -quality-level=Low -carla-rpc-port=20000 > "/workspace/artifacts/task20/carla/carla.log" 2>&1 &
echo "$!" > "/workspace/artifacts/task20/carla/carla.pid"
python - <<'PY'
import socket
import time

deadline = time.time() + 120
last_error = None
while time.time() < deadline:
    try:
        with socket.create_connection(("127.0.0.1", 20000), timeout=2):
            print("CARLA port 20000 is reachable")
            raise SystemExit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(1)
raise SystemExit(f"CARLA did not open port 20000 within 120s: {last_error}")
PY
