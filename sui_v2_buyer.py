"""DIR-020 — one REAL x402 v2 exact-scheme SETTLE on Sui testnet.

A fresh throwaway buyer wallet funds itself from the official testnet faucet,
signs a SplitCoins->TransferObjects tx paying the seller address 15000000 MIST
(0.015 SUI, sentiment price parity) with asset 0x2::sui::SUI, and relays
verify+settle through the hosted non-custodial x402 facilitator — the same
endpoints our server uses. Nothing simulated; digest verifiable on-chain.

Never touches existing wallet private keys (seller address only).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import httpx
from nacl.signing import SigningKey

from sui_a2a_pay import build_split_transfer_tx, sign
from sui_x402_v2 import b64e, settle_via_facilitator

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHQL = "https://graphql.testnet.sui.io/graphql"
FAUCET = "https://faucet.testnet.sui.io/v2/gas"
WALLET_FILE = os.path.join(ROOT, "sui_testnet_buyer_wallet.json")
AMOUNT = 15_000_000  # MIST (0.015 SUI)


def gql(query: str) -> dict:
    return httpx.post(GRAPHQL, json={"query": query}, timeout=30).json()


def balance(addr: str) -> int:
    out = gql('{ address(address: "%s") { balances { nodes { totalBalance } } } }' % addr)
    nodes = out["data"]["address"]["balances"]["nodes"]
    return sum(int(n["totalBalance"]) for n in nodes)


def gas_ref(addr: str) -> dict:
    out = gql('{ address(address: "%s") { objects(first: 1) { nodes { address version digest } } } }' % addr)
    nodes = out["data"]["address"]["objects"]["nodes"]
    if not nodes:
        raise RuntimeError(f"no gas objects for {addr}")
    n = nodes[0]
    return {"id": n["address"], "version": int(n["version"]), "digest": n["digest"]}


def seller_address() -> str:
    """Public pay-to address only — never reads key material.
    Honors SELLER_ADDRESS env for keyless hosts (runners)."""
    env = os.environ.get("SELLER_ADDRESS", "").strip()
    if env:
        return env
    with open(os.path.join(ROOT, "sui_seller_wallet.json")) as f:
        return json.load(f)["address"]


def create_or_load_wallet() -> tuple[SigningKey, str]:
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE) as f:
            w = json.load(f)
        return SigningKey(bytes(w["seed"])), w["address"]
    sk = SigningKey.generate()
    pub = bytes(sk.verify_key)
    addr = "0x" + hashlib.blake2b(b"\x00" + pub, digest_size=32).hexdigest()
    with open(WALLET_FILE, "w") as f:
        json.dump({
            "network": "sui-testnet",
            "address": addr,
            "seed": list(bytes(sk)),
            "warning": "TESTNET ONLY - throwaway buyer wallet",
        }, f, indent=2)
    return sk, addr


def fund_from_faucet(addr: str) -> tuple[bool, int]:
    """Returns (funded, suggested_wait_seconds_from_server)."""
    wait_s = 30
    try:
        r = httpx.post(FAUCET, json={"FixedAmountRequest": {"recipient": addr}},
                       headers={"Content-Type": "application/json"}, timeout=30)
        print("faucet:", r.status_code, r.text[:200])
        if r.status_code == 200:
            return balance(addr) > 0, 0
        # 429 bodies look like 'Too Many Requests! Wait for 52s'
        if "Wait for" in r.text:
            try:
                wait_s = int(r.text.split("Wait for")[1].strip().rstrip("sS").strip()) + 3
            except ValueError:
                pass
    except Exception as exc:
        print("faucet unreachable:", exc)
    return False, min(wait_s, 180)


def wait_for_funding(buyer: str, max_attempts: int = 8) -> int:
    """Adaptive faucet loop honoring server-advised waits; returns final balance."""
    bal = balance(buyer)
    attempts = 0
    while bal < AMOUNT and attempts < max_attempts:
        attempts += 1
        funded, wait_s = fund_from_faucet(buyer)
        bal = balance(buyer)
        if funded:
            break
        print(f"attempt {attempts}/{max_attempts} not funded yet; "
              f"server-advised wait {wait_s}s")
        if wait_s <= 0:
            wait_s = 15
        time.sleep(wait_s)
    return bal


def on_chain_check(digest: str, seller: str) -> None:
    q = '''query($d: Digest!) {
      transactionBlock(digest: $d) {
        balanceChanges { nodes { owner { address } amount coinType } }
      }
    }'''
    out = httpx.post(GRAPHQL, json={"query": q, "variables": {"d": digest}}, timeout=30).json()
    tb = ((out.get("data") or {}).get("transactionBlock")) or {}
    nodes = (tb.get("balanceChanges") or {}).get("nodes", [])
    print("on-chain balanceChanges for", digest)
    for ch in nodes:
        owner = (ch.get("owner") or {}).get("address")
        print(f"  {owner}: {ch['amount']} {ch['coinType']}")


def main() -> int:
    marker = os.path.join(ROOT, "org", "state", "DIRECTIVE_DIR020_DONE.txt")
    if os.path.exists(marker):
        with open(marker) as f:
            print("DIR-020 already proven; digest:", f.read().strip())
        return 0

    sk, buyer = create_or_load_wallet()
    seller = seller_address()
    print("buyer :", buyer)
    print("seller:", seller)

    bal = balance(buyer)
    print("buyer balance:", bal, "MIST")
    if bal < AMOUNT:
        bal = wait_for_funding(buyer)
    if bal < AMOUNT:
        print(f"UNFUNDED after faucet retries (balance={bal}, need>={AMOUNT}) "
              f"— exiting cleanly; rerun later (wallet persisted)")
        return 2

    reqs = {
        "scheme": "exact",
        "network": "sui:testnet",
        "amount": str(AMOUNT),
        "asset": "0x2::sui::SUI",
        "payTo": seller,
        "maxTimeoutSeconds": 600,
    }
    ref = gas_ref(buyer)
    print("gas object:", ref["id"], "v", ref["version"])
    tx_b64, sig = sign(sk, build_split_transfer_tx(buyer, seller, AMOUNT, ref))
    payload = {"x402Version": 2, "accepted": reqs,
               "payload": {"signature": sig, "transaction": tx_b64}}
    ok, result = settle_via_facilitator(b64e(payload), reqs)
    print((ok, result))
    if ok:
        digest = result.split()[0]
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w") as f:
            f.write(f"{digest} buyer={buyer} seller={seller} amount={AMOUNT} "
                    f"asset=0x2::sui::SUI network=sui:testnet\n")
        on_chain_check(digest, seller)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
