"""CHAINFEED — paid on-chain analytics for AI agents, powered by LIVE data
from real Base mainnet (mainnet.base.org).

Services sold via the same x402 402-flow:
  /v1/block-stats   $0.002  latest block number, gas base fee, tx count
  /v1/usdc-supply   $0.005  live USDC contract info on Base

Settlement is simulated (MockFacilitator) but every data point served is
genuine, fetched live at request time from the Base network.
"""

from __future__ import annotations

import base64
import json
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payment_core import MockFacilitator, PaymentPayload, PaymentRequirements

app = FastAPI(title="chainfeed", version="0.4.0")
facilitator = MockFacilitator()

RPC = "https://mainnet.base.org"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

_rpc = httpx.Client(timeout=10)
_cache: dict[str, tuple[float, dict]] = {}


def _b64(o): return base64.b64encode(json.dumps(o).encode()).decode()
def _unb64(s): return json.loads(base64.b64decode(s))


def rpc(method: str, params: list) -> dict:
    r = _rpc.post(RPC, json={"jsonrpc": "2.0", "method": method,
                             "params": params, "id": 1})
    return r.json().get("result", {})


def cached(key: str, ttl: float, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    val = fn()
    _cache[key] = (time.time(), val)
    return val


def block_stats() -> dict:
    n = int(rpc("eth_blockNumber", []), 16)
    blk = rpc("eth_getBlockByNumber", [hex(n), False])
    prev = rpc("eth_getBlockByNumber", [hex(n - 1), False])
    t_now, t_prev = int(blk["timestamp"], 16), int(prev["timestamp"], 16)
    return {
        "block": n,
        "transactions_in_block": len(blk.get("transactions", [])),
        "base_fee_gwei": round(int(blk.get("baseFeePerGas", "0x0"), 16) / 1e9, 6),
        "block_time_seconds": t_now - t_prev,
        "fetched_at": t_now,
    }


def usdc_info() -> dict:
    # eth_getBalance-style reads need ABI encoding; use code existence +
    # balanceOf via raw eth_call would need padding — keep to verifiable basics
    code = rpc("eth_getCode", [USDC_BASE, "latest"])
    n = int(rpc("eth_blockNumber", []), 16)
    return {
        "contract": USDC_BASE,
        "deployed_code_bytes": len(code) // 2 - 1,
        "verified_live_at_block": n,
        "note": "USDC native contract present on Base mainnet",
    }


SERVICES = {
    "/v1/block-stats": {"price": 0.002, "fn": lambda: cached("blk", 2.0, block_stats)},
    "/v1/usdc-info":   {"price": 0.005, "fn": lambda: cached("usdc", 60.0, usdc_info)},
}


@app.get("/health")
def health():
    try:
        n = int(rpc("eth_blockNumber", []), 16)
        return {"status": "ok", "base_mainnet_block": n}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/bazaar")
def bazaar():
    return {"services": [
        {"endpoint": ep, "price_usdc": cfg["price"], "data_source": "live Base mainnet RPC"}
        for ep, cfg in SERVICES.items()
    ]}


@app.get("/stats")
def stats():
    rev: dict[str, float] = {}
    for r in facilitator.settled:
        rev[r.get("service", "?")] = round(rev.get(r.get("service", "?"), 0) + r["amount_usdc"], 6)
    return {"total_settled_usdc": round(facilitator.total_settled_usdc, 6),
            "payments_settled": len(facilitator.settled),
            "revenue_by_service": rev}


@app.get("/{path:path}")
def paid(request: Request, path: str, q: str = ""):
    endpoint = f"/{path}"
    cfg = SERVICES.get(endpoint)
    if not cfg:
        return JSONResponse({"error": "unknown service"}, status_code=404)

    header = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("X-Payment")
    if not header:
        req = PaymentRequirements(resource=endpoint, amount_usdc=cfg["price"])
        return JSONResponse(status_code=402,
                            content={"error": "Payment Required", "accepts": req.to_dict()},
                            headers={"PAYMENT-REQUIRED": _b64(req.to_dict())})
    try:
        d = _unb64(header)
        payload = PaymentPayload(requirements=d["requirements"], payer=d["payer"],
                                 amount_usdc=d["amount_usdc"],
                                 timestamp=d["timestamp"], signature=d["signature"])
    except Exception as exc:
        return JSONResponse({"error": f"malformed payment: {exc}"}, status_code=400)

    receipt = facilitator.settle(payload)
    if not receipt["settled"]:
        return JSONResponse({"error": "rejected", "reason": receipt["reason"]}, status_code=402)

    receipt["service"] = endpoint
    try:
        result = cfg["fn"]()
    except Exception as exc:
        return JSONResponse({"error": f"upstream failure: {exc}"}, status_code=502)
    return JSONResponse(content=result, headers={"PAYMENT-RESPONSE": _b64(receipt)})
