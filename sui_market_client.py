"""Buyer agent for the real-settlement Sui market.

Discovers the bazaar, gets the 402 challenge (pay_to + MIST amount), executes
a REAL signed Sui transfer, retries with the tx digest, receives the service
result with an on-chain settlement receipt.
"""

from __future__ import annotations

import json
import os
import sys

import httpx
from nacl.signing import SigningKey

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sui_a2a_pay import build_split_transfer_tx, sign, execute, gas_ref  # noqa: E402
from suisettle import balance, LAMPORT  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:8604"

with open(os.path.join(ROOT, "sui_buyer_wallet.json")) as f:
    _bw = json.load(f)
SK = SigningKey(bytes(_bw["seed"]))
BUYER = _bw["address"]


def buy(endpoint: str, text: str) -> dict:
    with httpx.Client(timeout=60) as c:
        # 1. unpaid request -> 402 challenge
        r = c.get(BASE + endpoint, params={"text": text})
        if r.status_code != 402:
            return {"error": f"expected 402, got {r.status_code}"}
        challenge = r.json()
        pay_to, amount = challenge["pay_to"], challenge["amount_mist"]
        print(f"  402 challenge: pay {amount/LAMPORT} SUI to {pay_to[:14]}…")

        # 2. execute REAL on-chain transfer
        ref = gas_ref(BUYER)
        tx_bytes = build_split_transfer_tx(BUYER, pay_to, amount, ref)
        tx_b64, user_sig = sign(SK, tx_bytes)
        result = execute(tx_b64, user_sig)
        if "errors" in result:
            return {"error": f"tx failed: {result['errors']}"}
        effects = result["data"]["executeTransaction"]["effects"]
        digest = effects["digest"]
        status = effects["status"]
        print(f"  tx {digest} status={status}")

        # 3. retry with digest
        r2 = c.get(BASE + endpoint, params={"text": text},
                   headers={"X-SUI-TX-DIGEST": digest})
        out = r2.json()
        out["_http"] = r2.status_code
        return out


if __name__ == "__main__":
    print(f"buyer {BUYER} balance {balance(BUYER)/LAMPORT} SUI\n")
    for ep, text in [
        ("/v1/sentiment", "Agents paying agents on Sui is great, not a scam"),
        ("/v1/entity-extract", "Mysten built Sui while Virtuals stayed on Base"),
    ]:
        print(f"BUY {ep}")
        res = buy(ep, text)
        print(json.dumps(res, indent=2)[:400], "\n")
    print("market stats:", json.dumps(httpx.get(BASE + "/stats").json()))
