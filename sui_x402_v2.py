"""x402 v2 `exact` scheme support for the Sui rail (DIR-011).

Implements the standard x402 v2 dialect so stock clients can pay us:
challenge is a base64 `PAYMENT-REQUIRED` header, retry carries base64
`PAYMENT-SIGNATURE`, and settlement is delegated to the hosted non-custodial
facilitator (verify -> settle in testnet USDC). We never broadcast anything
ourselves and never touch keys.
"""

from __future__ import annotations

import base64
import json

import httpx
from fastapi.responses import JSONResponse

FACIL = "https://sui-facilitator.onrender.com"
TESTNET_USDC = (
    "0xa1ec7fc00a6f40db9693ad1415d0c193ad3906494428cf252621037bd7117e29::usdc::USDC"
)
NETWORK = "sui:testnet"
X402_VERSION = 2
MAX_TIMEOUT_SECONDS = 600

# Catalog prices in USDC atomic units (6 decimals): $0.015 / $0.030 / $0.075.
V2_PRICES = {
    "/v1/sentiment": "15000",
    "/v1/entity-extract": "30000",
    "/v1/summarize": "75000",
}


def b64d(s: str) -> str:
    """urlsafe-base64 string -> decoded UTF-8 text."""
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode()).decode()


def b64e(o: object) -> str:
    """JSON object -> urlsafe-base64 string."""
    raw = json.dumps(o, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _seller_address() -> str:
    # Address only; private keys are never read.
    with open("sui_seller_wallet.json") as f:
        return json.load(f)["address"]


def requirements(endpoint: str) -> dict:
    """PaymentRequirements for one endpoint (standard x402 v2 exact scheme)."""
    return {
        "scheme": "exact",
        "network": NETWORK,
        "amount": V2_PRICES[endpoint],
        "asset": TESTNET_USDC,
        "payTo": _seller_address(),
        "maxTimeoutSeconds": MAX_TIMEOUT_SECONDS,
    }


def challenge_402(reqs: dict) -> JSONResponse:
    """402 with a base64 PAYMENT-REQUIRED header (plus human-readable body)."""
    body = {
        "x402Version": X402_VERSION,
        "error": "payment_required",
        "accepts": [reqs],
        "scheme": "x402-v2-exact",
        "instructions": "Retry with header PAYMENT-SIGNATURE: <base64 "
                        "PaymentPayload> settled via the x402 facilitator",
    }
    return JSONResponse(
        status_code=402,
        content=body,
        headers={"PAYMENT-REQUIRED": b64e(body)},
    )


def settle_via_facilitator(payload_b64: str, reqs: dict) -> tuple[bool, str]:
    """Verify + settle a PAYMENT-SIGNATURE payload via the hosted facilitator.

    Returns (ok, digest_or_reason). Never broadcasts anything ourselves;
    all errors are returned as (False, reason), never raised.
    """
    try:
        payment_payload = json.loads(b64d(payload_b64))
    except Exception as exc:  # malformed payload
        return False, f"unparseable payment payload: {exc}"

    body = {
        "x402Version": X402_VERSION,
        "paymentPayload": payment_payload,
        "paymentRequirements": reqs,
    }
    try:
        vr = httpx.post(f"{FACIL}/verify", json=body, timeout=30).json()
    except Exception as exc:
        return False, f"facilitator verify unreachable: {exc}"
    if not vr.get("isValid"):
        return False, f"verify failed: {vr.get('invalidReason', vr)}"

    try:
        sr = httpx.post(f"{FACIL}/settle", json=body, timeout=60).json()
    except Exception as exc:
        return False, f"facilitator settle unreachable: {exc}"
    if not sr.get("success"):
        return False, f"settle failed: {sr.get('errorReason', sr)}"
    digest = sr.get("transaction") or sr.get("digest") or "settled"
    return True, f"{digest} payer={sr.get('payer', 'unknown')}"
