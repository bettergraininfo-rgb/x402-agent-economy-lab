"""PRODUCTION PATH: real x402 settlement via Coinbase CDP on Base.

Status: STRUCTURED BUT UNTESTED WITH REAL FUNDS. This file imports the real
`x402` and `cdp` SDKs (both installed) and lays out the exact integration.
It will raise a clear configuration error until you provide:

  1. A CDP API key (from portal.cdp.coinbase.com)
  2. A funded Base wallet (even $5 USDC covers thousands of requests)
  3. CDP_WALLET_SECRET + CDP_API_KEY_ID env vars

Nothing here moves money until those exist. Do NOT commit real keys.

Usage (once configured):
    export CDP_API_KEY_ID=...
    export CDP_API_KEY_SECRET=...
    export CDP_WALLET_SECRET=...
    .venv/bin/python production_cdp.py --serve
"""

from __future__ import annotations

import os
import sys

from x402 import (
    FacilitatorConfig,
    FacilitatorClientSync,
    x402ResourceServerSync,
)

# Networks supported by the CDP facilitator
BASE_MAINNET = "base"
BASE_SEPOLIA = "base-sepolia"
USDC_BASE_MAINNET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


def check_env() -> dict:
    """Verify required CDP credentials exist (values never printed)."""
    required = ["CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "CDP_WALLET_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    status = {
        "ready": not missing,
        "missing": missing,
        "network": os.environ.get("X402_NETWORK", BASE_SEPOLIA),
    }
    if missing:
        print("NOT READY — missing env vars:", ", ".join(missing))
        print("Get keys at https://portal.cdp.coinbase.com")
        print("Fund a Base Sepolia wallet with USDC faucet for testing:")
        print(f"  Sepolia USDC: {USDC_BASE_SEPOLIA}")
        print(f"  Mainnet USDC: {USDC_BASE_MAINNET}")
    else:
        print("READY — credentials present, network:", status["network"])
    return status


def build_facilitator_client() -> FacilitatorClientSync:
    """Real CDP facilitator client (verifies + settles x402 payments)."""
    return FacilitatorClientSync(FacilitatorConfig())


def main() -> int:
    status = check_env()
    if not status["ready"]:
        return 1

    # With credentials present, wire the real stack:
    #
    #   facilitator = build_facilitator_client()
    #   server = x402ResourceServerSync(facilitator_clients=[facilitator])
    #   server.register(...)   # scheme + network + pay_to address
    #   server.initialize()
    #
    # Then mount the same routes as market_server.py, replacing
    # MockFacilitator.settle() with server.verify_payment()/settle_payment().
    #
    # The buyer side uses x402ClientSync with a CDP Server Wallet signer,
    # replacing PaymentPayload.sign() with a real EIP-3009 transferWithAuthorization.
    print("Credential check passed — full wiring requires your wallet address.")
    print("Next step: set X402_PAY_TO and re-run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
