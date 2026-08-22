"""True agent-to-agent (A2A) commerce: two INDEPENDENT marketplace nodes,
each running its own facilitator and its own buyer-agent. Each node
discovers the other via /bazaar and purchases services through the complete
x402 flow. Revenue flows both directions — a genuine two-node agent economy.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from payment_core import MockFacilitator, PaymentPayload, PaymentRequirements


def _b64(o): return base64.b64encode(json.dumps(o).encode()).decode()
def _unb64(s): return json.loads(base64.b64decode(s))


# ------------------------------------------------------------ service impls

def svc_weather(city: str) -> dict:
    """Deterministic mock weather (alpha's specialty)."""
    temps = {"paris": 21, "tokyo": 27, "newyork": 18, "lagos": 31}
    t = temps.get(city.lower().replace(" ", ""), 20)
    return {"city": city, "temp_c": t, "forecast": "clear" if t > 22 else "cloudy"}


def svc_translate(text: str) -> dict:
    """Toy EN->FR dictionary translation (beta's specialty)."""
    d = {"hello": "bonjour", "agent": "agent", "money": "argent",
         "market": "marché", "the": "le", "is": "est", "open": "ouvert"}
    return {"french": " ".join(d.get(w.lower(), w) for w in text.split())}


def svc_hash(text: str) -> dict:
    import hashlib
    return {"sha256": hashlib.sha256(text.encode()).hexdigest()[:32]}


def make_node(name: str, wallet: str, services: dict) -> FastAPI:
    app = FastAPI(title=f"a2a-node-{name}")
    fac = MockFacilitator()
    app.state.fac = fac

    @app.get("/health")
    def health():
        return {"node": name, "services": len(services)}

    @app.get("/bazaar")
    def bazaar():
        return {"node": name, "services": [
            {"endpoint": ep, "price_usdc": cfg["price"], "description": cfg["desc"]}
            for ep, cfg in services.items()
        ]}

    @app.get("/stats")
    def stats():
        rev = {}
        for r in fac.settled:
            rev[r.get("service", "?")] = round(rev.get(r.get("service", "?"), 0) + r["amount_usdc"], 6)
        return {"node": name, "earned_usdc": round(fac.total_settled_usdc, 6),
                "jobs_completed": len(fac.settled), "revenue_by_service": rev}

    @app.get("/{path:path}")
    def paid(request: Request, path: str, q: str = ""):
        endpoint = f"/{path}"
        cfg = services.get(endpoint)
        if not cfg:
            return JSONResponse({"error": "unknown"}, status_code=404)
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
            return JSONResponse({"error": f"malformed: {exc}"}, status_code=400)
        receipt = fac.settle(payload)
        if not receipt["settled"]:
            return JSONResponse({"error": "rejected", "reason": receipt["reason"]}, status_code=402)
        receipt["service"] = endpoint
        return JSONResponse(content=cfg["fn"](q), headers={"PAYMENT-RESPONSE": _b64(receipt)})

    return app


# Node ALPHA: weather + hashing          Node BETA: translation
ALPHA = make_node("alpha", "0xNODE-ALPHA", {
    "/v1/weather": {"price": 0.004, "fn": svc_weather, "desc": "City weather lookup"},
    "/v1/hash":    {"price": 0.001, "fn": lambda t: svc_hash(t), "desc": "SHA256 digest"},
})
BETA = make_node("beta", "0xNODE-BETA", {
    "/v1/translate": {"price": 0.003, "fn": svc_translate, "desc": "EN->FR translation"},
})


def run_server(app, port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


class NodeAgent:
    """Each node's embedded buyer: discovers the OTHER node and buys."""

    def __init__(self, my_name: str, wallet: str, peer_url: str, budget: float):
        self.my_name, self.wallet = my_name, wallet
        self.peer_url, self.budget, self.spent = peer_url, budget, 0.0
        self.log: list[str] = []

    def shop_once(self):
        cat = httpx.get(f"{self.peer_url}/bazaar", timeout=5).json()
        for svc in cat["services"]:
            price = float(svc["price_usdc"])
            if self.spent + price > self.budget:
                self.log.append(f"budget cap reached (${self.spent:.4f})")
                return
            params = {"q": {
                "/v1/weather": "tokyo", "/v1/hash": "agent-money",
                "/v1/translate": "the market is open",
            }.get(svc["endpoint"], "test")}
            with httpx.Client(timeout=10) as c:
                r = c.get(self.peer_url + svc["endpoint"], params=params)
                if r.status_code != 402:
                    continue
                accepts = _unb64(r.headers["PAYMENT-REQUIRED"])
                p = PaymentPayload(requirements=accepts, payer=self.wallet, amount_usdc=price)
                p.sign()
                r2 = c.get(self.peer_url + svc["endpoint"], params=params,
                           headers={"PAYMENT-SIGNATURE": _b64(p.to_dict())})
                if r2.status_code == 200:
                    self.spent += price
                    rc = _unb64(next(v for k, v in r2.headers.items()
                                     if k.lower() == "payment-response"))
                    self.log.append(
                        f"{cat['node']}{svc['endpoint']} -> {json.dumps(r2.json())} "
                        f"[${price}] tx={rc['tx_hash'][:10]}")
                else:
                    self.log.append(f"{svc['endpoint']} FAILED: {r2.status_code}")


if __name__ == "__main__":
    threads = [
        threading.Thread(target=run_server, args=(ALPHA, 8601), daemon=True),
        threading.Thread(target=run_server, args=(BETA, 8602), daemon=True),
    ]
    for t in threads:
        t.start()
    time.sleep(2.5)

    print("=== A2A economy booting: alpha(:8601) <-> beta(:8602) ===\n")
    agent_alpha = NodeAgent("alpha", "0xNODE-ALPHA", "http://127.0.0.1:8602", budget=0.02)
    agent_beta = NodeAgent("beta", "0xNODE-BETA", "http://127.0.0.1:8601", budget=0.02)

    # Three rounds of mutual commerce
    for rnd in range(3):
        print(f"--- round {rnd+1} ---")
        agent_alpha.shop_once()
        agent_beta.shop_once()

    print("\nAlpha's purchases from Beta:")
    for line in agent_alpha.log:
        print("  ", line)
    print("\nBeta's purchases from Alpha:")
    for line in agent_beta.log:
        print("  ", line)

    print("\n=== Final ledger ===")
    for port, label in [(8601, "alpha"), (8602, "beta")]:
        s = httpx.get(f"http://127.0.0.1:{port}/stats", timeout=5).json()
        print(json.dumps(s, indent=2))

    total_earned = (httpx.get("http://127.0.0.1:8601/stats").json()["earned_usdc"]
                    + httpx.get("http://127.0.0.1:8602/stats").json()["earned_usdc"])
    total_spent = agent_alpha.spent + agent_beta.spent
    print(f"\nEconomy check: total earned ${total_earned:.4f} vs total spent ${total_spent:.4f} "
          f"{'BALANCED ✓' if abs(total_earned-total_spent) < 1e-9 else 'MISMATCH ✗'}")
