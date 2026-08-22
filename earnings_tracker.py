"""Earnings tracker for the Sui agent economy.

Reports the total on-chain holdings of all agent wallets (buyer + seller)
plus cumulative marketplace revenue. Designed for cron: quiet when nothing
changed, verbose when there's something to report.
"""

from __future__ import annotations

import json
import os
import sys

import httpx

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHQL = "https://graphql.devnet.sui.io/graphql"
STATE_FILE = os.path.join(ROOT, ".earnings_state.json")
LAMPORT = 1_000_000_000


def gql(query: str) -> dict:
    return httpx.post(GRAPHQL, json={"query": query}, timeout=30).json()


def balance(addr: str) -> int:
    out = gql('{ address(address: "%s") { balances { nodes { totalBalance } } } }' % addr)
    nodes = out.get("data", {}).get("address", {}).get("balances", {}).get("nodes", [])
    return sum(int(n["totalBalance"]) for n in nodes)


def wallets() -> list[tuple[str, str]]:
    out = []
    for name in ("sui_buyer_wallet.json", "sui_seller_wallet.json"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            with open(p) as f:
                w = json.load(f)
            out.append((name.replace("sui_", "").replace("_wallet.json", ""), w["address"]))
    return out


if __name__ == "__main__":
    rows = []
    total = 0
    for name, addr in wallets():
        bal = balance(addr)
        total += bal
        rows.append((name, addr, bal))
        print(f"{name:8s} {addr}  {bal/LAMPORT:.4f} SUI")

    prev = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            prev = json.load(f).get("total", 0)
    with open(STATE_FILE, "w") as f:
        json.dump({"total": total}, f)

    delta = total - prev
    print(f"\nTOTAL: {total/LAMPORT:.4f} SUI (delta since last check: {delta/LAMPORT:+.4f})")

    # Exit code signals change: cron prompt decides verbosity
    sys.exit(0 if delta != 0 else 2)
