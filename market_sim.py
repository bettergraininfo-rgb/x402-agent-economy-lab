"""Buyer swarm + demand-shock simulation against the dynamic-pricing market.

Phase A: normal shopping (all three services get steady traffic)
Phase B: demand shock — whales stop buying summarize entirely;
         sentiment demand doubles. Watch prices adapt via /price-history.
"""

from __future__ import annotations

import base64
import json
import random

import httpx

from payment_core import PaymentPayload

BASE = "http://127.0.0.1:8503"


def _b64(o): return base64.b64encode(json.dumps(o).encode()).decode()
def _unb64(s): return json.loads(base64.b64decode(s))


class Buyer:
    def __init__(self, name, wallet, budget, weights: dict[str, float]):
        self.name, self.wallet = name, wallet
        self.budget, self.spent = budget, 0.0
        self.weights = weights  # endpoint -> probability weight

    def shop(self):
        catalog = httpx.get(f"{BASE}/bazaar").json()["services"]
        eps, ws = zip(*[(s["endpoint"], self.weights.get(s["endpoint"], 0.05)) for s in catalog])
        pick_eps = random.choices(eps, weights=ws, k=1)[0]
        svc = next(s for s in catalog if s["endpoint"] == pick_eps)

        texts = {
            "/v1/sentiment": "agents are great, love the gains",
            "/v1/summarize": "Sentence one about crypto. Sentence two about agents paying agents. Sentence three is filler. Sentence four concludes.",
            "/v1/entity-extract": "Coinbase built Base while Virtuals shipped agents",
            "/v1/report": "Coinbase built Base. Virtuals shipped agents. Solana is fast.",
            "/v1/batch": "agents are great ||| rug pull scam ||| love the gains",
        }
        url, params = BASE + pick_eps, {"text": texts[pick_eps]}
        with httpx.Client(timeout=10) as c:
            r = c.get(url, params=params)
            if r.status_code != 402:
                return
            accepts = _unb64(r.headers["PAYMENT-REQUIRED"])
            price = float(accepts["amount_usdc"])
            if self.spent + price > self.budget:
                return
            p = PaymentPayload(requirements=accepts, payer=self.wallet, amount_usdc=price)
            p.sign()
            r2 = c.get(url, params=params, headers={"PAYMENT-SIGNATURE": _b64(p.to_dict())})
            if r2.status_code == 200:
                self.spent += price


def swarm_round(buyers, label):
    for b in buyers:
        if b.spent < b.budget:
            b.shop()
    prices = {s["endpoint"]: s["price_usdc"] for s in httpx.get(f"{BASE}/bazaar").json()["services"]}
    print(f"[{label}] prices: {json.dumps(prices)}")


if __name__ == "__main__":
    random.seed(42)

    normal_weights = lambda: {
        "/v1/sentiment": 0.4, "/v1/summarize": 0.3, "/v1/entity-extract": 0.3,
    }
    shock_weights = {
        "/v1/sentiment": 0.75, "/v1/summarize": 0.02, "/v1/entity-extract": 0.23,
    }

    buyers_a = [Buyer("A-Scrooge", "0xA1", 0.010, normal_weights()),
                Buyer("A-Research", "0xA2", 0.030, normal_weights()),
                Buyer("A-Whale", "0xA3", 0.100, normal_weights())]
    buyers_b = [Buyer("B-Scrooge", "0xB1", 0.010, shock_weights),
                Buyer("B-Research", "0xB2", 0.030, shock_weights),
                Buyer("B-Whale", "0xB3", 0.100, shock_weights)]

    print("=== Phase A: baseline demand ===")
    for i in range(12):
        swarm_round(buyers_a, f"A{i+1:02d}")

    print("\n=== Phase B: demand SHOCK (sentiment surges, summarize dies) ===")
    for i in range(12):
        swarm_round(buyers_b, f"B{i+1:02d}")

    hist = httpx.get(f"{BASE}/price-history").json()["history"]
    stats = httpx.get(f"{BASE}/stats").json()
    spent = sum(b.spent for b in buyers_a + buyers_b)

    print("\n=== Price adaptation timeline ===")
    for h in hist:
        prices = "  ".join(
            f"{ep.replace('/v1/', '')}=${p:.6f}" for ep, p in sorted(h["prices"].items())
        )
        print(f" after {h['after_payments']:2d} payments: {prices}")

    print("\n=== Final marketplace stats ===")
    print(json.dumps(stats, indent=2))
    print(f"\nTotal consumer spending across both phases: ${spent:.4f}")
