"""Negative tests: the facilitator must reject tampered + replayed payments."""

import httpx
from payment_core import PaymentPayload

from agent_client import _b64, _unb64

BASE = "http://127.0.0.1:8402"

# 1. Get fresh requirements
r = httpx.get(f"{BASE}/v1/sentiment", params={"text": "test"})
assert r.status_code == 402
accepts = _unb64(r.headers["PAYMENT-REQUIRED"])

# 2. Build a valid signed payload
payload = PaymentPayload(requirements=accepts, payer="0xEVE", amount_usdc=0.01)
payload.sign()

def send(p: PaymentPayload):
    return httpx.get(
        f"{BASE}/v1/sentiment",
        params={"text": "hello world"},
        headers={"PAYMENT-SIGNATURE": _b64(p.to_dict())},
    )

# 3. Valid payment -> 200
r = send(payload)
print("valid payment      ->", r.status_code, "(expect 200)")
assert r.status_code == 200

# 4. Replay same payment -> 402 rejected
r = send(payload)
print("replayed payment   ->", r.status_code, "(expect 402)", r.json()["reason"])
assert r.status_code == 402 and "replay" in r.json()["reason"]

# 5. Tampered amount -> signature mismatch -> 402
accepts2 = dict(accepts)
tampered = PaymentPayload(requirements=accepts2, payer="0xEVE", amount_usdc=0.01)
tampered.sign()
tampered.amount_usdc = 0.000001  # mutate AFTER signing
r = send(tampered)
print("tampered payment   ->", r.status_code, "(expect 402)", r.json()["reason"])
assert r.status_code == 402

# 6. Underpayment with valid signature -> 402
accepts3 = dict(accepts)
cheap = PaymentPayload(requirements=accepts3, payer="0xEVE", amount_usdc=0.0001)
cheap.sign()
r = send(cheap)
print("underpayment       ->", r.status_code, "(expect 402)", r.json()["reason"])
assert r.status_code == 402

print("\nALL SECURITY TESTS PASSED")
