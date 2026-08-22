"""Autonomous agent economy over the bazaar.

Three buyer agents with distinct budgets and service preferences discover
services via /bazaar, then purchase repeatedly until their budgets run out.
Each purchase goes through the full x402 402->sign->retry->settle flow.
"""

from __future__ import annotations

import base64
import json
import random

import httpx

from payment_core import PaymentPayload

BASE = "http://127.0.0.1:8502"


def _b64(o): return base64.b64encode(json.dumps(o).encode()).decode()
def _unb64(s): return json.loads(base64.b64decode(s))


class BuyerAgent:
    def __init__(self, name: str, wallet: str, budget: float,
                 preferred: list[str], max_price: float):
        self.name, self.wallet = name, wallet
        self.budget, self.spent = budget, 0.0
        self.preferred, self.max_price = preferred, max_price
        self.purchases: list[dict] = []

    def shop(self) -> None:
        """Discovery step: fetch the bazaar catalog."""
        catalog = httpx.get(f"{BASE}/bazaar").json()["services"]
        affordable = [
            s for s in catalog
            if s["endpoint"] in self.preferred or random.random() < 0.3
        ]
        affordable = [s for s in affordable if s["price_usdc"] <= self.max_price]
        if not affordable:
            return
        pick = min(affordable, key=lambda s: s["price_usdc"])  # bargain hunter
        self.buy(pick)

    def buy(self, service: dict) -> None:
        texts = {
            "/v1/sentiment": "Virtuals agents are great but the crash was terrible",
            "/v1/summarize": "AI agents are transforming payments. x402 enables micropayments over HTTP. Coinbase processed millions of payments. The protocol uses HTTP 402. Stablecoins settle instantly.",
            "/v1/entity-extract": "Coinbase built Base where Virtuals agents trade across Solana and Ethereum",
        }
        url, params = BASE + service["endpoint"], {"text": texts[service["endpoint"]]}

        with httpx.Client(timeout=10) as c:
            r = c.get(url, params=params)
            if r.status_code != 402:
                self.purchases.append({"service": service["endpoint"], "status": r.status_code})
                return
            accepts = _unb64(r.headers["PAYMENT-REQUIRED"])
            price = float(accepts["amount_usdc"])
            if self.spent + price > self.budget:
                self.purchases.append({"service": service["endpoint"], "status": "budget-refused"})
                return
            payload = PaymentPayload(requirements=accepts, payer=self.wallet, amount_usdc=price)
            payload.sign()
            r2 = c.get(url, params=params, headers={"PAYMENT-SIGNATURE": _b64(payload.to_dict())})
            ok = r2.status_code == 200
            if ok:
                self.spent += price
            self.purchases.append({
                "service": service["endpoint"],
                "status": "ok" if ok else f"http-{r2.status_code}",
                "paid": price if ok else 0.0,
                "result": r2.json() if ok else None,
            })


AGENTS = [
    BuyerAgent("Scrooge",   "0xBUYER-SCROOGE",  budget=0.010, preferred=["/v1/sentiment"],              max_price=0.001),
    BuyerAgent("Researcher","0xBUYER-RESEARCH", budget=0.030, preferred=["/v1/summarize"],              max_price=0.005),
    BuyerAgent("Whale",     "0xBUYER-WHALE",    budget=0.100, preferred=["/v1/sentiment", "/v1/entity-extract", "/v1/summarize"], max_price=0.01),
]

if __name__ == "__main__":
    print("=== Agent economy session starting ===\n")
    rounds = 8
    for rnd in range(rounds):
        alive = [a for a in AGENTS if a.spent < a.budget]
        if not alive:
            break
        for a in alive:
            a.shop()

    for a in AGENTS:
        ok = sum(1 for p in a.purchases if p["status"] == "ok")
        refused = sum(1 for p in a.purchases if p["status"] == "budget-refused")
        print(f"[{a.name:10s}] spent ${a.spent:.4f} of ${a.budget:.3f} | "
              f"{ok} purchases, {refused} budget-refusals")

    stats = httpx.get(f"{BASE}/stats").json()
    print("\n=== Marketplace revenue ===")
    print(json.dumps(stats, indent=2))

    sample = next((p for a in AGENTS for p in a.purchases if p["status"] == "ok"), None)
    if sample:
        print(f"\nSample deliverable ({sample['service']}): {json.dumps(sample['result'])}")
