"""Daily agent-economy run: boots a fresh bazaar, runs the buyer swarm,
reports revenue + price adaptation. Designed to be invoked by cron.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

import httpx

BASE = "http://127.0.0.1:8503"
ROOT = "/home/jackie/x402-agent-service"
PY = f"{ROOT}/.venv/bin/python"


def wait_ready(timeout_s: int = 15) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    # 1. Boot a fresh market server (kill anything stale on the port first)
    subprocess.run(["pkill", "-f", "uvicorn market_server:app"], check=False)
    time.sleep(1)
    server = subprocess.Popen(
        [f"{ROOT}/.venv/bin/uvicorn", "market_server:app",
         "--host", "127.0.0.1", "--port", "8503"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_ready():
            print("ERROR: market server failed to start")
            return 1

        # 2. Run the swarm simulation (baseline + shock phases)
        sim = subprocess.run([PY, f"{ROOT}/market_sim.py"],
                             capture_output=True, text=True, timeout=300)
        print(sim.stdout[-3000:])
        if sim.returncode != 0:
            print("SIM STDERR:", sim.stderr[-1000:])
            return 1

        # 3. Final stats snapshot
        stats = httpx.get(f"{BASE}/stats", timeout=5).json()
        hist = httpx.get(f"{BASE}/price-history", timeout=5).json()
        print("=== DAILY SUMMARY ===")
        print(json.dumps({"stats": stats, "reprice_events": len(hist["history"])}, indent=2))
        return 0
    finally:
        server.terminate()


if __name__ == "__main__":
    sys.exit(main())
