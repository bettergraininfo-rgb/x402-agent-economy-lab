"""x402-style paid API server.

Endpoints:
  GET /v1/sentiment?text=...   -> paid endpoint ($0.01/request, x402 flow)
  GET /health                  -> free
  GET /stats                   -> free (revenue dashboard)

Flow (mirrors https://x402.org):
  1. Client GETs without payment        -> 402 + PAYMENT-REQUIRED header
  2. Client signs payment, retries      -> server verifies via facilitator
  3. Payment settled on "chain"         -> 200 + PAYMENT-RESPONSE header
"""

from __future__ import annotations

import base64
import json

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from payment_core import MockFacilitator, PaymentRequirements

app = FastAPI(title="paid-sentiment-api", version="0.1.0")
facilitator = MockFacilitator()

PRICE_USDC = 0.01


def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode()).decode()


def _unb64(s: str) -> dict:
    return json.loads(base64.b64decode(s))


# ---------------------------------------------------------------- free APIs

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict:
    return {
        "total_settled_usdc": round(facilitator.total_settled_usdc, 4),
        "payments_settled": len(facilitator.settled),
        "price_per_request_usdc": PRICE_USDC,
    }


# ------------------------------------------------------------ the paid API

def analyze_sentiment(text: str) -> dict:
    """The actual service being sold: a small lexicon sentiment scorer."""
    positive = {
        "good", "great", "excellent", "love", "amazing", "wonderful",
        "fantastic", "happy", "best", "awesome", "profit", "win", "gain",
    }
    negative = {
        "bad", "terrible", "awful", "hate", "horrible", "worst", "sad",
        "loss", "lose", "crash", "scam", "rug", "fail",
    }
    words = [w.strip(".,!?;:").lower() for w in text.split()]
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    if pos > neg:
        label, score = "positive", min(1.0, 0.4 + 0.2 * (pos - neg))
    elif neg > pos:
        label, score = "negative", -min(1.0, 0.4 + 0.2 * (neg - pos))
    else:
        label, score = "neutral", 0.0
    return {"label": label, "score": round(score, 2), "tokens": len(words)}


@app.get("/v1/sentiment")
def sentiment(request: Request, text: str = "") -> Response:
    if not text:
        return JSONResponse({"error": "missing ?text= parameter"}, status_code=400)

    payment_header = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get(
        "X-Payment"
    )

    # --- Step 1: no payment attached -> 402 with requirements -------------
    if not payment_header:
        req = PaymentRequirements(
            resource="/v1/sentiment", amount_usdc=PRICE_USDC
        )
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "accepts": req.to_dict(),
            },
            headers={"PAYMENT-REQUIRED": _b64(req.to_dict())},
        )

    # --- Step 2: payment attached -> verify + settle ----------------------
    try:
        payload_dict = _unb64(payment_header)
        from payment_core import PaymentPayload

        payload = PaymentPayload(
            requirements=payload_dict["requirements"],
            payer=payload_dict["payer"],
            amount_usdc=payload_dict["amount_usdc"],
            timestamp=payload_dict["timestamp"],
            signature=payload_dict["signature"],
        )
    except Exception as exc:  # malformed payment
        return JSONResponse({"error": f"malformed payment: {exc}"}, status_code=400)

    receipt = facilitator.settle(payload)
    if not receipt["settled"]:
        return JSONResponse(
            {"error": "payment rejected", "reason": receipt["reason"]},
            status_code=402,
        )

    # --- Step 3: serve the paid resource ----------------------------------
    result = analyze_sentiment(text)
    return JSONResponse(
        content=result,
        headers={"PAYMENT-RESPONSE": _b64(receipt)},
    )
