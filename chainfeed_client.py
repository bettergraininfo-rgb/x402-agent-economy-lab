"""Agent buying LIVE Base mainnet data through the x402 payment loop."""
from __future__ import annotations
import base64, json, os, sys
import httpx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from payment_core import PaymentPayload

BASE = "http://127.0.0.1:8504"
WALLET = "0xdC0750D5fB649bab3B8b02d31CDab12Dcae0cC51"  # the agent's testnet wallet

_b64 = lambda o: base64.b64encode(json.dumps(o).encode()).decode()
_unb64 = lambda s: json.loads(base64.b64decode(s))

def buy(endpoint: str):
    with httpx.Client(timeout=15) as c:
        r = c.get(BASE + endpoint)
        if r.status_code != 402:
            return {"status": r.status_code, "body": r.json()}
        accepts = _unb64(r.headers["PAYMENT-REQUIRED"])
        p = PaymentPayload(requirements=accepts, payer=WALLET,
                           amount_usdc=float(accepts["amount_usdc"]))
        p.sign()
        r2 = c.get(BASE + endpoint, headers={"PAYMENT-SIGNATURE": _b64(p.to_dict())})
        out = {"status": r2.status_code, "body": r2.json()}
        if "PAYMENT-RESPONSE" in r2.headers or any(
                k.lower() == "payment-response" for k in r2.headers):
            for k, v in r2.headers.items():
                if k.lower() == "payment-response":
                    out["receipt"] = _unb64(v)
        return out

if __name__ == "__main__":
    print("=== ChainFeed: agent purchasing live on-chain data ===\n")
    for ep in ["/v1/block-stats", "/v1/usdc-info"]:
        res = buy(ep)
        print(f"[{ep}] HTTP {res['status']}")
        print(json.dumps(res["body"], indent=2))
        if "receipt" in res:
            rc = res["receipt"]
            print(f"  -> paid ${rc['amount_usdc']}, tx {rc['tx_hash'][:16]}…")
        print()
    print("Marketplace stats:", json.dumps(httpx.get(f"{BASE}/stats").json(), indent=2))
