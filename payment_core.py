"""Shared payment types for the x402-style pay-per-use flow.

This is a local simulation of the x402 protocol (https://x402.org) so the
full client/server payment loop can be exercised without real funds.
Swapping `MockFacilitator` for a real verifier/settler (e.g. Coinbase CDP
Facilitator on Base with USDC) is the production path.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field

# In production this secret lives in a KMS/HSM; here it just makes the
# simulation non-trivial.
_SIGNING_KEY = b"local-sim-key-do-not-use-in-prod"
REPLAY_WINDOW_SECONDS = 300


@dataclass
class PaymentRequirements:
    """What the server demands before serving a request (the 402 body)."""

    resource: str          # e.g. "/v1/sentiment"
    scheme: str = "exact"  # x402 "exact" scheme: pay a fixed amount
    amount_usdc: float = 0.01
    pay_to: str = "0xSIMULATED-SELLER-ADDRESS"
    network: str = "base-sepolia"
    nonce: str = ""

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = hashlib.sha256(
                f"{self.resource}{time.time_ns()}".encode()
            ).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {
            "scheme": self.scheme,
            "resource": self.resource,
            "amount_usdc": self.amount_usdc,
            "pay_to": self.pay_to,
            "network": self.network,
            "nonce": self.nonce,
        }


@dataclass
class PaymentPayload:
    """What the client signs and attaches to the retried request."""

    requirements: dict
    payer: str
    amount_usdc: float
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def signing_material(self) -> str:
        return json.dumps(
            {
                "requirements": self.requirements,
                "payer": self.payer,
                "amount_usdc": self.amount_usdc,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
        )

    def sign(self, key: bytes = _SIGNING_KEY) -> None:
        self.signature = hmac.new(
            key, self.signing_material().encode(), hashlib.sha256
        ).hexdigest()

    def to_dict(self) -> dict:
        return {
            "requirements": self.requirements,
            "payer": self.payer,
            "amount_usdc": self.amount_usdc,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


class MockFacilitator:
    """Verifies + settles payments. Production: CDP Facilitator on Base."""

    def __init__(self, key: bytes = _SIGNING_KEY) -> None:
        self.key = key
        self.settled: list[dict] = []
        self.total_settled_usdc = 0.0
        self._seen_nonces: set[str] = set()

    def verify(self, payload: PaymentPayload) -> tuple[bool, str]:
        # 1. signature check (tamper evidence)
        expected = hmac.new(
            self.key, payload.signing_material().encode(), hashlib.sha256
        ).hexdigest()
        if not payload.signature or not hmac.compare_digest(expected, payload.signature):
            return False, "invalid signature"

        # 2. amount matches what was asked
        asked = payload.requirements.get("amount_usdc")
        if payload.amount_usdc < float(asked):
            return False, f"underpayment: sent {payload.amount_usdc}, required {asked}"

        # 3. replay protection
        nonce = payload.requirements.get("nonce", "")
        if nonce in self._seen_nonces:
            return False, "replayed payment (nonce already settled)"
        if time.time() - payload.timestamp > REPLAY_WINDOW_SECONDS:
            return False, "payment expired"

        return True, "ok"

    def settle(self, payload: PaymentPayload) -> dict:
        ok, reason = self.verify(payload)
        if not ok:
            return {"settled": False, "reason": reason}
        self._seen_nonces.add(payload.requirements["nonce"])
        self.total_settled_usdc += payload.amount_usdc
        receipt = {
            "settled": True,
            "tx_hash": hashlib.sha256(payload.signing_material().encode()).hexdigest()[:32],
            "amount_usdc": payload.amount_usdc,
            "payer": payload.payer,
        }
        self.settled.append(receipt)
        return receipt
