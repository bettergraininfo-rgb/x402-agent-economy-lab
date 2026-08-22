"""Agent Bazaar: a multi-service x402-style marketplace.

Sellers register services with per-service pricing; buyers discover them via
/bazaar and pay per request through the same 402 flow as before.

Endpoints:
  GET /bazaar                      -> service discovery (free)
  GET /v1/sentiment?text=...       -> $0.001/req
  GET /v1/summarize?text=...       -> $0.005/req
  GET /v1/entity-extract?text=...  -> $0.002/req
  GET /stats                       -> per-service revenue dashboard
"""

from __future__ import annotations

import base64
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payment_core import MockFacilitator, PaymentPayload, PaymentRequirements

app = FastAPI(title="agent-bazaar", version="0.2.0")
facilitator = MockFacilitator()


def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode()).decode()


def _unb64(s: str) -> dict:
    return json.loads(base64.b64decode(s))


# ------------------------------------------------------------- the services

def svc_sentiment(text: str) -> dict:
    pos = {"good", "great", "excellent", "love", "amazing", "win", "gain", "profit"}
    neg = {"bad", "terrible", "awful", "hate", "worst", "loss", "crash", "scam", "rug"}
    words = [w.strip(".,!?;:").lower() for w in text.split()]
    p = sum(w in pos for w in words)
    n = sum(w in neg for w in words)
    label = "positive" if p > n else "negative" if n > p else "neutral"
    score = round(min(1.0, 0.4 + 0.2 * abs(p - n)) * (1 if p > n else -1 if n > p else 0), 2)
    return {"label": label, "score": score}


def svc_summarize(text: str) -> dict:
    sents = [s.strip() for s in text.replace("! ", ". ").replace("? ", ". ").split(". ") if s.strip()]
    keep = max(1, len(sents) // 3)
    scored = sorted(
        range(len(sents)),
        key=lambda i: -len(set(sents[i].lower().split()) - {"the", "a", "an", "of", "and"}),
    )
    summary = ". ".join(sents[i] for i in sorted(scored[:keep]))
    return {"summary": summary, "original_sentences": len(sents)}


def svc_entities(text: str) -> dict:
    caps = [w.strip(".,!?;:") for w in text.split() if w[:1].isupper() and w.strip(".,!?;:").isalpha()]
    known_orgs = {"Coinbase", "Base", "Virtuals", "Injective", "Solana", "Ethereum", "Cardano"}
    return {
        "organizations": sorted(set(caps) & known_orgs),
        "proper_nouns": sorted({c for c in caps if c not in known_orgs}),
    }


SERVICES = {
    "/v1/sentiment":       {"price": 0.001, "seller": "svc-alpha",   "fn": svc_sentiment, "desc": "Lexicon sentiment scoring"},
    "/v1/summarize":       {"price": 0.005, "seller": "svc-beta",    "fn": svc_summarize, "desc": "Extractive summarization"},
    "/v1/entity-extract":  {"price": 0.002, "seller": "svc-alpha",   "fn": svc_entities,  "desc": "Org/proper-noun extraction"},
}


# ------------------------------------------------------------------ routes

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "services": len(SERVICES)}


@app.get("/bazaar")
def bazaar() -> dict:
    """Discovery: what agents can buy here."""
    return {
        "services": [
            {
                "endpoint": ep,
                "description": cfg["desc"],
                "price_usdc": cfg["price"],
                "scheme": "exact",
                "network": "base-sepolia",
                "pay_to": f"0xSELLER-{cfg['seller'].upper()}",
            }
            for ep, cfg in SERVICES.items()
        ]
    }


@app.get("/stats")
def stats() -> dict:
    by_seller: dict[str, float] = {}
    for r in facilitator.settled:
        by_seller[r.get("service", "?")] = by_seller.get(r.get("service", "?"), 0.0) + r["amount_usdc"]
    return {
        "total_settled_usdc": round(facilitator.total_settled_usdc, 6),
        "payments_settled": len(facilitator.settled),
        "revenue_by_service": {k: round(v, 6) for k, v in by_seller.items()},
    }


@app.get("/{service_path:path}")
def paid_service(request: Request, service_path: str, text: str = ""):
    endpoint = f"/{service_path}"
    if not text:
        return JSONResponse({"error": "missing ?text= parameter"}, status_code=400)

    cfg = SERVICES.get(endpoint)
    if not cfg:
        return JSONResponse({"error": "unknown service"}, status_code=404)

    payment_header = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("X-Payment")
    if not payment_header:
        req = PaymentRequirements(resource=endpoint, amount_usdc=cfg["price"])
        return JSONResponse(
            status_code=402,
            content={"error": "Payment Required", "accepts": req.to_dict()},
            headers={"PAYMENT-REQUIRED": _b64(req.to_dict())},
        )

    try:
        d = _unb64(payment_header)
        payload = PaymentPayload(
            requirements=d["requirements"], payer=d["payer"],
            amount_usdc=d["amount_usdc"], timestamp=d["timestamp"],
            signature=d["signature"],
        )
    except Exception as exc:
        return JSONResponse({"error": f"malformed payment: {exc}"}, status_code=400)

    receipt = facilitator.settle(payload)
    if not receipt["settled"]:
        return JSONResponse({"error": "payment rejected", "reason": receipt["reason"]}, status_code=402)

    # Attribute revenue to the selling service
    receipt["service"] = endpoint
    result = cfg["fn"](text)
    return JSONResponse(content=result, headers={"PAYMENT-RESPONSE": _b64(receipt)})
