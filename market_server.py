"""Market server with DYNAMIC PRICING.

Sellers watch conversion behavior and reprice:
  - service bought a lot -> price rises (up to 3x base)
  - service ignored      -> price falls (down to 0.4x base)
Repricing happens every REPRICE_EVERY settled payments.

Endpoints:
  GET /bazaar          -> current catalog w/ live prices
  GET /v1/*            -> paid endpoints (same 402 flow)
  GET /stats           -> revenue
  GET /price-history   -> how prices adapted over time
"""

from __future__ import annotations

import base64
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payment_core import MockFacilitator, PaymentPayload, PaymentRequirements
from bazaar import svc_sentiment, svc_summarize, svc_entities, svc_report, svc_batch

app = FastAPI(title="agent-bazaar-dynamic", version="0.3.0")
facilitator = MockFacilitator()

REPRICE_EVERY = 6
MIN_FACTOR, MAX_FACTOR = 0.4, 3.0

SERVICES = {
    "/v1/sentiment":      {"base_price": 0.015, "price": 0.015, "fn": svc_sentiment},
    "/v1/summarize":      {"base_price": 0.075, "price": 0.075, "fn": svc_summarize},
    "/v1/entity-extract": {"base_price": 0.030, "price": 0.030, "fn": svc_entities},
    "/v1/report":         {"base_price": 0.020, "price": 0.020, "fn": svc_report},
    "/v1/batch":          {"base_price": 0.050, "price": 0.050, "fn": svc_batch},
}
# views vs buys per service since last reprice
demand = {ep: {"views": 0, "buys": 0} for ep in SERVICES}
price_history: list[dict] = []


def _b64(o): return base64.b64encode(json.dumps(o).encode()).decode()
def _unb64(s): return json.loads(base64.b64decode(s))


def reprice() -> None:
    """Conversion-driven pricing: buy-rate sets the multiplier."""
    global demand
    changed = {}
    for ep, cfg in SERVICES.items():
        d = demand[ep]
        conv = d["buys"] / max(1, d["views"])
        # conv=1.0 -> 2x price, conv=0.33 -> ~0.9x, conv=0 -> 0.4x
        factor = max(MIN_FACTOR, min(MAX_FACTOR, 0.4 + 1.6 * conv))
        cfg["price"] = round(cfg["base_price"] * factor, 6)
        changed[ep] = cfg["price"]
    price_history.append({"after_payments": len(facilitator.settled), "prices": dict(changed)})
    demand = {ep: {"views": 0, "buys": 0} for ep in SERVICES}


@app.get("/health")
def health():
    return {"status": "ok", "payments": len(facilitator.settled)}


@app.get("/bazaar")
def bazaar():
    return {"services": [
        {"endpoint": ep, "price_usdc": cfg["price"], "base_price_usdc": cfg["base_price"]}
        for ep, cfg in SERVICES.items()
    ]}


@app.get("/stats")
def stats():
    return {
        "total_settled_usdc": round(facilitator.total_settled_usdc, 6),
        "payments_settled": len(facilitator.settled),
        "revenue_by_service": _rev_by_service(),
    }


def _rev_by_service():
    out: dict[str, float] = {}
    for r in facilitator.settled:
        out[r.get("service", "?")] = round(out.get(r.get("service", "?"), 0.0) + r["amount_usdc"], 6)
    return out


@app.get("/price-history")
def phist():
    return {"history": price_history}


@app.get("/{service_path:path}")
def paid(request: Request, service_path: str, text: str = ""):
    endpoint = f"/{service_path}"
    cfg = SERVICES.get(endpoint)
    if not text:
        return JSONResponse({"error": "missing ?text="}, status_code=400)
    if not cfg:
        return JSONResponse({"error": "unknown service"}, status_code=404)

    header = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("X-Payment")
    if not header:
        demand[endpoint]["views"] += 1
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
        return JSONResponse({"error": "payment rejected", "reason": receipt["reason"]}, status_code=402)

    receipt["service"] = endpoint
    receipt["price_paid"] = payload.amount_usdc
    demand[endpoint]["buys"] += 1
    if len(facilitator.settled) % REPRICE_EVERY == 0:
        reprice()
    return JSONResponse(content=cfg["fn"](text), headers={"PAYMENT-RESPONSE": _b64(receipt)})
