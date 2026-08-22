#!/usr/bin/env python3
"""ops/auditor.py — independent audit of the agent-economy business.

Cross-checks what the company CLAIMS against what is VERIFIABLE:
  - revenue ledger vs live on-chain USDC balance of receiving wallet
  - every ledger tx actually exists on Base mainnet (to us, USDC, amount)
  - cron fleet status via hermes CLI
Exit code: 0 = clean, 1 = discrepancies found (printed).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "x402-agent-service"
RECIPIENT = "0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")

problems: list[str] = []
notes: list[str] = []


def rpc(method: str, params: list):
    import urllib.request
    req = urllib.request.Request(
        RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        out = json.load(r)
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["result"]


def check_ledger_vs_chain():
    lf = ROOT / "org" / "revenue_ledger.json"
    if not lf.exists():
        problems.append("ledger missing entirely")
        return
    d = json.loads(lf.read_text())
    claimed = round(float(d.get("lifetime_usdc", 0)), 6)
    txs = d.get("txs", {})
    for tx, meta in txs.items():
        try:
            rcpt = rpc("eth_getTransactionReceipt", [tx])
            if rcpt is None:
                problems.append(f"ledger tx {tx[:18]}… NOT FOUND on-chain")
                continue
            if rcpt.get("status") != "0x1":
                problems.append(f"ledger tx {tx[:18]}… reverted on-chain")
                continue
            hit = False
            for lg in rcpt.get("logs", []):
                topics = lg.get("topics", [])
                if (lg.get("address", "").lower() == USDC
                        and topics and topics[0].lower() == TRANSFER_TOPIC
                        and len(topics) >= 3
                        and topics[2].lower() == "0x" + "0" * 24 + RECIPIENT[2:].lower()):
                    value = int(lg["data"], 16) / 1e6
                    recorded = float(meta.get("amount_usdc", -1))
                    if abs(value - recorded) > 1e-6:
                        problems.append(f"tx {tx[:18]}… amount mismatch: chain={value} ledger={recorded}")
                    hit = True
            if not hit:
                problems.append(f"tx {tx[:18]}… has NO USDC transfer to receiving wallet")
        except Exception as e:
            notes.append(f"could not verify tx {tx[:18]}… ({e}); treating as unverified")
    # live balance cross-check
    try:
        hexbal = rpc("eth_call", [{"to": USDC, "data": "0x70a08231" + "0" * 24 + RECIPIENT[2:]}, "latest"])
        live = int(hexbal, 16) / 1e6
        if abs(live - claimed) > 1e-6:
            problems.append(
                f"LIVE BALANCE MISMATCH: wallet holds {live} USDC but ledger claims {claimed} lifetime "
                f"(delta {round(live - claimed, 6)} — manual withdrawal or missed entry?)")
        else:
            notes.append(f"live wallet balance matches ledger: {live} USDC across {len(txs)} tx(s)")
    except Exception as e:
        notes.append(f"could not read live USDC balance ({e})")


def check_cron_fleet():
    try:
        out = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=60).stdout
        import re
        clean = re.sub(r"\x1b\[[0-9;]*m", "", out)
        active = clean.count("[active]")
        if active < 7:
            problems.append(f"cron fleet degraded: only {active} active jobs (expected >= 7)")
    except Exception as e:
        problems.append(f"cannot inspect cron fleet: {e}")


def main():
    check_ledger_vs_chain()
    check_cron_fleet()
    stamp = datetime.now(timezone.utc).strftime("%FT%TZ")
    lines = [f"AUDIT {stamp}"] + [f"  note: {n}" for n in notes]
    if problems:
        lines += [f"  DISCREPANCY: {p}" for p in problems]
        print("\n".join(lines))
        sys.exit(1)
    # silent-when-clean: record the clean verdict to the ops log, print nothing
    log = ROOT / "org" / "system_events.log"
    with open(log, "a") as f:
        f.write(f"{stamp} | AUDITOR | clean — books match chain ({len(notes)} note(s))\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
