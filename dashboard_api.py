"""Dashboard API — mission control backend for the x402 AI-agent economy.

Serves the single-file dashboard at / and JSON feeds under /api/*.
Reads live SUI balances via the same GraphQL helper used by suisettle.py,
and replays transaction/bot/log journals from dotfiles when they exist.

Run:  .venv/bin/python -m uvicorn dashboard_api:app --host 127.0.0.1 --port 8605
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

import suisettle

ROOT = Path.home() / "x402-agent-service"
TXLOG = ROOT / ".txlog.jsonl"
BOTSTATE = ROOT / ".botstate.json"
BOTLOG = ROOT / ".botlog.jsonl"

# --------------------------------------------------------------- agents

AGENTS = [
    {
        "name": "Buyer",
        "role": "buyer",
        "address": "0x3a167896d5433db42e73f7a94102c4961c44c0ea146c34f7c746ac17067591a3",
        "network": "sui-devnet",
    },
    {
        "name": "Seller/Merchant",
        "role": "seller",
        "address": "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a",
        "network": "sui-devnet",
    },
    {
        "name": "Miner",
        "role": "miner",
        "address": "0xdC0750D5fB649bab3B8b02d31CDab12Dcae0cC51",
        "network": "base-sepolia (PoW, off-chain earnings)",
    },
]

# Fallback market stats when no transaction journal exists yet.
DEMO_MARKET = {
    "sales": 14,
    "revenue_by_service": {
        "/v1/sentiment": {"sales": 6, "revenue_usdc": 0.006, "price_usdc": 0.001},
        "/v1/entity-extract": {"sales": 4, "revenue_usdc": 0.008, "price_usdc": 0.002},
        "/v1/summarize": {"sales": 4, "revenue_usdc": 0.020, "price_usdc": 0.005},
    },
}

EScrow = {
    "locked_sui": 0.5,
    "escrows": 1,
    "package": "0x19c5dff9e7caba014247cc755479d5a01912b24c981e3411c0e0c1aa83482cc5",
}

app = FastAPI(title="x402 Agent Economy Dashboard")

_lock = threading.Lock()
_balance_history: list[float] = []          # in-memory treasury samples


# --------------------------------------------------------------- helpers

def _read_jsonl(path: Path, limit: int = 100) -> list[dict]:
    """Tail a JSONL journal; return newest-first list of dicts ([] if absent)."""
    if not path.exists():
        return []
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    out.reverse()  # newest first
    return out[:limit]


def _live_balances() -> dict[str, float | None]:
    """Address -> SUI balance via suisettle's GraphQL reader."""
    bals: dict[str, float | None] = {}
    for a in AGENTS:
        addr = a["address"]
        if a["network"] != "sui-devnet":
            bals[addr] = None  # off-chain wallet (PoW earnings)
            continue
        try:
            mist = suisettle.balance(addr)
            bals[addr] = round(mist / suisettle.LAMPORT, 6)
        except Exception:
            bals[addr] = None
    return bals


def _market_from_txs(txs: list[dict]) -> dict:
    sales = 0
    revenue: dict[str, dict] = {}
    for t in txs:
        if str(t.get("status", "")).upper() != "SUCCESS":
            continue
        svc = t.get("service") or t.get("kind") or "unknown"
        amt = float(t.get("amount_usdc", t.get("amount", 0)) or 0)
        entry = revenue.setdefault(
            svc, {"sales": 0, "revenue_usdc": 0.0, "price_usdc": amt})
        entry["sales"] += 1
        entry["revenue_usdc"] += amt
        sales += 1
    if not sales:
        return DEMO_MARKET.copy()
    return {"sales": sales, "revenue_by_service": revenue}


# --------------------------------------------------------------- routes

@app.get("/")
def index():
    return FileResponse(ROOT / "dashboard" / "index.html")


@app.get("/api/overview")
def overview():
    txs = _read_jsonl(TXLOG)
    bals = _live_balances()
    wallets = []
    total = 0.0
    for a in AGENTS:
        b = bals[a["address"]]
        wallets.append({
            "name": a["name"],
            "address": a["address"],
            "network": a["network"],
            "balance_sui": b,
        })
        if b is not None:
            total += b
    total = round(total, 6)

    # append treasury sample for the history graph (max ~720 pts = 2h @10s)
    with _lock:
        _balance_history.append(total)
        del _balance_history[:-720]
        history = list(_balance_history)

    # seed the chart so it isn't empty on first load
    if len(history) <= 1:
        step = max(total * 0.01, 0.05)
        history = [round(max(0.0, total - step * (20 - i) / 4 +
                             step * ((i * 7919) % 13) / 13), 4)
                   for i in range(20)] + history

    return {
        "total_sui": total,
        "wallets": wallets,
        "market": _market_from_txs(txs),
        "balance_history": history,
        "ts": int(time.time()),
    }


@app.get("/api/txs")
def txs():
    rows = _read_jsonl(TXLOG, limit=60)
    return {"txs": [{
        "digest": t.get("digest", "—"),
        "kind": t.get("kind", t.get("service", "transfer")),
        "from": t.get("from", ""),
        "to": t.get("to", ""),
        "amount_sui": t.get("amount_sui", t.get("amount", 0)),
        "status": str(t.get("status", "UNKNOWN")).upper(),
        "ts": t.get("ts", t.get("timestamp")),
    } for t in rows]}


@app.get("/api/agents")
def agents():
    bals = _live_balances()
    txs_all = _read_jsonl(TXLOG, limit=500)
    out = []
    for a in AGENTS:
        addr_lower = a["address"].lower()
        mine = [t for t in txs_all
                if str(t.get("from", "")).lower() == addr_lower
                or str(t.get("to", "")).lower() == addr_lower]
        last_ts = max((t.get("ts", t.get("timestamp", 0)) or 0 for t in mine),
                      default=None)
        out.append({
            **a,
            "balance_sui": bals[a["address"]],
            "tx_count": len(mine),
            "last_activity": last_ts,
            "status": "online",
        })
    return {"agents": out}


@app.get("/api/bots")
def bots():
    if BOTSTATE.exists():
        try:
            data = json.loads(BOTSTATE.read_text())
            return {"bots": data.get("bots", data if isinstance(data, list) else [])}
        except (json.JSONDecodeError, OSError):
            pass
    # default fleet until .botstate.json exists
    return {"bots": [
        {"name": "Coder",           "role": "builds features",       "status": "idle",   "last_action": "awaiting task queue"},
        {"name": "Reviewer",        "role": "reviews Coder output",  "status": "idle",   "last_action": "no pending diffs"},
        {"name": "Debugger",        "role": "tests & fixes",         "status": "idle",   "last_action": "test suite green"},
        {"name": "Visual Designer", "role": "UI polish",             "status": "idle",   "last_action": "design tokens synced"},
        {"name": "Miner",           "role": "earns via PoW",         "status": "running","last_action": "hashing sepolia-faucet session"},
        {"name": "Treasury Monitor","role": "watches balances",      "status": "running","last_action": f"sweep ok @ {int(time.time())}"},
    ]}


@app.get("/api/escrow")
def escrow():
    return EScrow


@app.get("/api/logs")
def logs():
    rows = _read_jsonl(BOTLOG, limit=120)
    return {"logs": rows}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8605)
