"""Autonomous agent client that consumes the x402-style paid API.

Demonstrates the full agent payment loop:
  1. GET resource -> receives 402 + PAYMENT-REQUIRED
  2. Parses requirements, signs a PaymentPayload (its own "wallet")
  3. Retries with PAYMENT-SIGNATURE header
  4. Gets result + settlement receipt

The agent tracks its own budget and refuses to overspend.
"""

from __future__ import annotations

import base64
import json

import httpx

from payment_core import PaymentPayload

AGENT_WALLET = "0xAGENT-WALLET-0001"
AGENT_BUDGET_USDC = 0.50  # hard spending cap
spent_usdc = 0.0


def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode()).decode()


def _unb64(s: str) -> dict:
    return json.loads(base64.b64decode(s))


def paid_get(url: str, params: dict) -> tuple[int, dict, dict]:
    """x402-aware GET. Returns (status, body, response_headers)."""
    global spent_usdc

    with httpx.Client(timeout=10) as client:
        # Attempt 1: no payment
        r = client.get(url, params=params)
        if r.status_code != 402:
            return r.status_code, r.json(), dict(r.headers)

        # Parse the 402 payment requirements
        accepts = _unb64(r.headers["PAYMENT-REQUIRED"])
        price = float(accepts["amount_usdc"])

        # Budget guardrail: the agent decides whether the price is worth it
        if spent_usdc + price > AGENT_BUDGET_USDC:
            return 0, {"error": "budget exhausted, agent refusing to pay"}, {}

        # Sign payment (simulated wallet key)
        payload = PaymentPayload(
            requirements=accepts,
            payer=AGENT_WALLET,
            amount_usdc=price,
        )
        payload.sign()

        # Attempt 2: retry with payment attached
        r2 = client.get(
            url,
            params=params,
            headers={"PAYMENT-SIGNATURE": _b64(payload.to_dict())},
        )
        if r2.status_code == 200:
            spent_usdc += price
        return r2.status_code, r2.json(), dict(r2.headers)


def get_header(headers: dict, name: str) -> str | None:
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return None


def run_batch(texts: list[str], base_url: str) -> None:
    print(f"=== Agent {AGENT_WALLET} | budget ${AGENT_BUDGET_USDC:.2f} ===\n")
    for text in texts:
        status, body, headers = paid_get(f"{base_url}/v1/sentiment", {"text": text})
        if status == 200:
            receipt = _unb64(get_header(headers, "PAYMENT-RESPONSE") or "{}")
            print(f"IN : {text!r}")
            print(f"OUT: {body}  [paid ${receipt['amount_usdc']}, tx {receipt['tx_hash'][:12]}…]")
        else:
            print(f"IN : {text!r}")
            print(f"ERR: {status} {body}")
        print()

    # Revenue check from the seller side
    r = httpx.get(f"{base_url}/stats")
    print("=== Seller stats ===")
    print(json.dumps(r.json(), indent=2))
    print(f"\n=== Agent spent: ${spent_usdc:.2f} of ${AGENT_BUDGET_USDC:.2f} budget ===")


if __name__ == "__main__":
    run_batch(
        [
            "I love this protocol, it is amazing and great",
            "total scam, worst crash ever, terrible",
            "the market closed flat today",
        ],
        "http://127.0.0.1:8402",
    )
