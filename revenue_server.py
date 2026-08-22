"""revenue_server.py — REAL-MONEY x402-style API server on Base mainnet.

Accepts actual on-chain USDC payments (eip-3009 transferWithAuthorization or
plain EIP-1559 ERC-20 transfers to our receiving address). Verifies every
payment on-chain via RPC before serving. No mocks.

Endpoints:
  GET  /bazaar            -> catalog + live prices (free)
  GET  /health            -> liveness + revenue stats
  POST /v1/sentiment      -> $0.015/call
  POST /v1/entity-extract -> $0.030/call
  POST /v1/summarize      -> $0.075/call
  POST /v1/report         -> $0.020/call (premium)
  POST /v1/batch          -> $0.050/call (premium)

Payment flow (x402-compatible shape):
  1. Client POSTs without payment -> 402 + X-Payment-Required header:
     {recipient, usdc, amount_usdc, amount_units, chain, memo, methods}
  2. Client pays USDC on Base to `recipient` (memo = its tx hash) and
     retries with header  X-Payment: <tx_hash>
  3. Server verifies the tx ON-CHAIN: to==recipient, token==USDC,
     value>=price, status=1, block recent, tx hash unused (replay guard).
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bazaar import svc_sentiment, svc_summarize, svc_entities, svc_report, svc_batch

app = FastAPI(title="agent-economy-revenue", version="1.0.0-real")

WALLET_FILE = Path(__file__).parent / "org" / "wallet_base_mainnet.json"
WALLET = json.loads(WALLET_FILE.read_text())
RECIPIENT = WALLET["address"].lower()

RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # native USDC, Base mainnet
USDC_TOPIC = ("0x" + "0" * 24 + USDC[2:].lower())  # ERC-20 Transfer topic1 (padded)
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

SERVICES = {
    "/v1/sentiment":      {"price": 0.015, "fn": svc_sentiment},
    "/v1/entity-extract": {"price": 0.030, "fn": svc_entities},
    "/v1/summarize":      {"price": 0.075, "fn": svc_summarize},
    "/v1/report":         {"price": 0.020, "fn": svc_report},
    "/v1/batch":          {"price": 0.050, "fn": svc_batch},
}

LEDGER = Path(__file__).parent / "org" / "revenue_ledger.json"
LEDGER_LOCK = Path(__file__).parent / "org" / ".revenue_ledger.lock"


def _load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"lifetime_usdc": 0.0, "sales": 0, "txs": {}, "by_endpoint": {}}


def _save_ledger(d: dict) -> None:
    LEDGER.write_text(json.dumps(d, indent=2))


def _record(tx: str, endpoint: str, amount: float) -> dict:
    d = _load_ledger()
    if tx in d["txs"]:
        return d["txs"][tx]
    d["txs"][tx] = {
        "endpoint": endpoint, "amount_usdc": amount, "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    d["lifetime_usdc"] = round(d["lifetime_usdc"] + amount, 6)
    d["sales"] += 1
    d["by_endpoint"][endpoint] = d["by_endpoint"].get(endpoint, 0) + amount
    _save_ledger(d)
    return d["txs"][tx]


async def _rpc(method: str, params: list) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        r.raise_for_status()
        out = r.json()
    if "error" in out:
        raise RuntimeError(f"RPC error: {out['error']}")
    return out["result"]


async def verify_payment(tx_hash: str, needed_units: int) -> tuple[bool, str, float | None]:
    """Verify an on-chain USDC transfer to RECIPIENT covering needed_units.

    Returns (ok, reason, amount_usdc).
    """
    if not (tx_hash.startswith("0x") and len(tx_hash) == 66):
        return False, "malformed tx hash", None
    try:
        rcpt = await _rpc("eth_getTransactionReceipt", [tx_hash])
    except Exception as e:
        return False, f"rpc unavailable: {e}", None
    if rcpt is None:
        return False, "tx not found (unmined or wrong network)", None
    if rcpt.get("status") != "0x1":
        return False, "tx reverted", None
    # freshness: must be within last ~1 hour of blocks
    try:
        head = int(await _rpc("eth_blockNumber", []), 16)
    except Exception:
        head = None
    blk = int(rcpt["blockNumber"], 16)
    if head is not None and head - blk > 1800:  # ~1h on Base (2s blocks)
        return False, "tx too old", None
    logs = rcpt.get("logs", [])
    for lg in logs:
        if (lg.get("address", "").lower() == USDC
                and lg.get("topics", [""])[0].lower() == TRANSFER_TOPIC
                and len(lg.get("topics", [])) >= 3
                and lg["topics"][2].lower() == ("0x" + "0" * 24 + RECIPIENT[2:])):
            value = int(lg["data"], 16)
            if value >= needed_units:
                return True, "ok", value / 1e6
            return False, f"underpaid: got {value/1e6} USDC", None
    return False, "no USDC transfer to recipient in tx", None


def _units(price_usdc: float) -> int:
    return int(round(price_usdc * 1e6))


def _402(endpoint: str) -> JSONResponse:
    cfg = SERVICES[endpoint]
    return JSONResponse({
        "error": "payment required",
        "accepts": {
            "scheme": "exact",
            "network": "base-mainnet",
            "token": "USDC",
            "extra": {"name": "USDC", "decimals": 6},
            "pay_to": WALLET["address"],
            "amount_usdc": cfg["price"],
            "amount_units": _units(cfg["price"]),
            "memo": "send USDC on Base, retry with X-Payment: <your tx hash>",
        },
    }, status_code=402, headers={
        "X-Payment-Required": json.dumps({
            "pay_to": WALLET["address"], "amount_units": _units(cfg["price"]),
            "token": USDC, "network": "base-mainnet"}),
    })


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "agent-economy NLP micro-services (REAL Base-mainnet USDC rail)",
        "description": ("Machine-payable NLP APIs paid in REAL USDC on Base "
                        "mainnet. Unauthenticated request returns HTTP 402 "
                        "with accepts[] payment requirements."),
        "catalog": "/bazaar", "health": "/health",
        "repo": "https://github.com/bettergraininfo-rgb/x402-agent-economy-lab",
        "endpoints": [ep for ep in SERVICES],
    }


@app.get("/.well-known/x402", include_in_schema=False)
@app.get("/.well-known/x402.json", include_in_schema=False)
def well_known_x402(request: Request):
    base = str(request.base_url).rstrip("/")
    if request.headers.get("x-forwarded-proto", "").lower() == "https":
        base = base.replace("http://", "https://", 1)
    usd = {"/v1/sentiment": 0.015, "/v1/entity-extract": 0.030,
           "/v1/summarize": 0.075, "/v1/report": 0.02, "/v1/batch": 0.05}
    return {
        "spec": "agent402-service-manifest/1", "version": 1,
        "resources": [
            {"url": f"{base}{ep}", "method": "GET", "price": usd[ep],
             "name": ep.lstrip("/"),
             "description": ("Pay-per-call NLP: sentiment score, entity "
                             "extraction, summarization, report, batch — "
                             "REAL USDC on Base mainnet.")}
            for ep in SERVICES
        ],
        "payment": ("exact USDC transfer on Base mainnet - unauthenticated "
                    "request returns HTTP 402 with accepts[] requirements"),
    }


@app.get("/health", include_in_schema=False)
def health():
    d = _load_ledger()
    return {"status": "ok", "real_money": True, "network": "base-mainnet",
            "lifetime_usdc": d["lifetime_usdc"], "sales": d["sales"],
            "recipient": WALLET["address"]}


@app.get("/bazaar", include_in_schema=False)
def bazaar():
    return {"network": "base-mainnet", "token": "USDC", "services": [
        {"endpoint": ep, "price_usdc": cfg["price"]}
        for ep, cfg in SERVICES.items()
    ]}


@app.post("/v1/{endpoint}")
async def serve(endpoint: str, request: Request):
    path = f"/v1/{endpoint}"
    if path not in SERVICES:
        return JSONResponse({"error": "unknown endpoint"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON body required"}, status_code=400)
    return await _authorize_and_serve(path, request, body)


@app.get("/v1/{endpoint}")
async def serve_get(endpoint: str, request: Request):
    path = f"/v1/{endpoint}"
    if path not in SERVICES:
        return JSONResponse({"error": "unknown endpoint"}, status_code=404)
    return await _authorize_and_serve(path, request,
                                      {"text": request.query_params.get("text", "")})


async def _authorize_and_serve(path: str, request: Request, body: dict):
    """Single payment-verification + replay-guard + ledger path for POST and GET."""
    cfg = SERVICES[path]

    tx_hash = request.headers.get("x-payment", "").strip()
    if not tx_hash:
        return _402(path)

    ok, reason, amount = await verify_payment(tx_hash, _units(cfg["price"]))
    if not ok:
        return JSONResponse({"error": "payment rejected", "reason": reason}, status_code=402,
                            headers={"X-Payment-Required": json.dumps({
                                "pay_to": WALLET["address"],
                                "amount_units": _units(cfg["price"]),
                                "token": USDC, "network": "base-mainnet"})})

    ledger = _load_ledger()
    if tx_hash in ledger["txs"]:
        return JSONResponse({"error": "payment already used (replay protection)"}, status_code=402)
    _record(tx_hash, path, amount or cfg["price"])

    # ---- serve the actual work ----
    result = (cfg["fn"](body.get("text", ""))
              if not isinstance(cfg["fn"], str) else {"error": "unimplemented"})
    return JSONResponse({"paid_usdc": amount or cfg["price"], "tx": tx_hash, "result": result})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8610)
