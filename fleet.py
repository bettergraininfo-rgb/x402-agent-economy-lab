"""Fleet coordination primitives for the bot workforce.

Handshake pattern:
  - Coder writes .build_complete marker when done
  - Debugger polls for the marker (not the files), with timeout
  - Marker contains status, files touched, and test instructions

This eliminates the race where the debugger times out before the coder
finishes.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path(os.environ.get("FLEET_ROOT", "/home/jackie/x402-agent-service"))
MARKER = ROOT / ".build_complete"
STATE = ROOT / ".botstate.json"
LOG = ROOT / ".botlog.jsonl"


def log_event(bot: str, event: str) -> None:
    """Append to the shared bot log (appears on dashboard System Log)."""
    entry = json.dumps({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bot": bot,
        "event": event,
    })
    with open(LOG, "a") as f:
        f.write(entry + "\n")


def signal_done(bot: str, summary: str, files: list[str] | None = None) -> None:
    """Coder calls this when its work is complete."""
    MARKER.write_text(json.dumps({
        "bot": bot,
        "summary": summary,
        "files": files or [],
        "ts": time.time(),
    }, indent=2))
    log_event(bot, f"BUILD COMPLETE: {summary}")


def wait_for_signal(timeout_s: int = 900, poll_s: int = 15) -> dict | None:
    """Debugger calls this; returns marker contents or None on timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if MARKER.exists():
            return json.loads(MARKER.read_text())
        time.sleep(poll_s)
    return None


def clear_signal() -> None:
    if MARKER.exists():
        MARKER.unlink()


def set_status(bot: str, status: str, last_action: str) -> None:
    """Update one bot's row in .botstate.json (dashboard Workforce panel)."""
    data = {"bots": []}
    if STATE.exists():
        data = json.loads(STATE.read_text())
    bots = {b["name"]: b for b in data.get("bots", [])}
    bots.setdefault(bot, {"name": bot, "role": "", "status": "idle",
                          "last_action": ""})
    bots[bot]["status"] = status
    bots[bot]["last_action"] = last_action
    data["bots"] = list(bots.values())
    STATE.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    # demo: set all six bots' current state
    set_status("Coder", "idle", "awaiting next task")
    set_status("Reviewer", "idle", "queue empty")
    set_status("Debugger", "idle", "all tests passing")
    set_status("VisualDesigner", "idle", "theme v1 applied")
    set_status("Miner", "scheduled", "next PoW run via GitHub Actions")
    set_status("TreasuryMonitor", "running", "watching Sui devnet every 15min")
    log_event("Fleet", "coordination layer online")
    print("fleet coordination ready")
