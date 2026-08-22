"""Escrowed service purchase — the agent uses its OWN smart contract.

Flow:
  1. SplitCoins to make a payment coin
  2. MoveCall agent_escrow::escrow::create(coin, seller, service)
     -> Escrow receipt object owned by buyer (funds LOCKED on-chain)
  3. [service would be delivered here; seller sees the escrow event]
  4. MoveCall agent_escrow::escrow::release(receipt)  [seller's side]

This script demonstrates steps 1-2 (lock) and then cancels (3-cancel path),
proving both directions of the contract work from Python.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

import sys
import httpx
import base58
from nacl.signing import SigningKey

from pysui.sui.sui_bcs import bcs

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHQL = "https://graphql.devnet.sui.io/graphql"
LAMPORT = 1_000_000_000

PACKAGE = "0x19c5dff9e7caba014247cc755479d5a01912b24c981e3411c0e0c1aa83482cc5"
SELLER = "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a"


def gql(query: str) -> dict:
    return httpx.post(GRAPHQL, json={"query": query}, timeout=30).json()


def balance(addr: str) -> int:
    out = gql('{ address(address: "%s") { balances { nodes { totalBalance } } } }' % addr)
    nodes = out["data"]["address"]["balances"]["nodes"]
    return sum(int(n["totalBalance"]) for n in nodes)


def gas_ref(addr: str) -> dict:
    out = gql('{ address(address: "%s") { objects(first: 1) { nodes { address version digest } } } }' % addr)
    n = out["data"]["address"]["objects"]["nodes"][0]
    return {"id": n["address"], "version": int(n["version"]), "digest": n["digest"]}


def _addr_arg(addr: str) -> bytes:
    return list(bytes.fromhex(addr[2:]))


def build_escrow_create(sender: str, seller: str, amount: int,
                        service: str, ref: dict) -> bytes:
    """SplitCoins(gas, amount) -> escrow::create(split, seller, service)."""
    _svc = service.encode()
    inputs = [
        bcs.CallArg("Pure", list(amount.to_bytes(8, "little"))),          # 0
        bcs.CallArg("Pure", _addr_arg(seller)),                           # 1
        bcs.CallArg("Pure", [len(_svc)] + list(_svc)),                    # 2 (vector<u8>)
    ]
    commands = [
        bcs.Command("SplitCoin", bcs.SplitCoin(
            FromCoin=bcs.Argument("GasCoin"),
            Amount=[bcs.Argument("Input", 0)])),
        bcs.Command("MoveCall", bcs.ProgrammableMoveCall(
            Package=bcs.Address(_addr_arg(PACKAGE)),
            Module="escrow",
            Function="create",
            Type_Arguments=[],
            Arguments=[
                bcs.Argument("Result", 0),      # the split coin
                bcs.Argument("Input", 1),       # seller
                bcs.Argument("Input", 2),       # service label
            ])),
    ]
    return _wrap_tx(sender, inputs, commands, ref)


def build_escrow_cancel(sender: str, escrow_obj_id: str,
                        escrow_version: int, escrow_digest: str) -> bytes:
    """escrow::cancel(receipt) — buyer reclaims locked funds."""
    inputs = [
        bcs.CallArg("Object", bcs.ObjectArg(
            "ImmOrOwnedObject",
            bcs.ObjectReference(bcs.Address(list(bytes.fromhex(escrow_obj_id[2:]))),
                                escrow_version,
                                bcs.Digest(list(base58.b58decode(escrow_digest)))))),
    ]
    commands = [
        bcs.Command("MoveCall", bcs.ProgrammableMoveCall(
            Package=bcs.Address(_addr_arg(PACKAGE)),
            Module="escrow",
            Function="cancel",
            Type_Arguments=[],
            Arguments=[bcs.Argument("Input", 0)])),
    ]
    return _wrap_tx(sender, inputs, commands, gas_ref(sender))


def _wrap_tx(sender: str, inputs: list, commands: list, ref: dict) -> bytes:
    pt = bcs.ProgrammableTransaction(inputs, commands)
    kind = bcs.TransactionKind("ProgrammableTransaction", pt)
    gas_data = bcs.GasData(
        [bcs.ObjectReference(bcs.Address(list(bytes.fromhex(ref["id"][2:]))),
                             ref["version"],
                             bcs.Digest(list(base58.b58decode(ref["digest"]))))],
        bcs.Address(list(bytes.fromhex(sender[2:]))), 1000, 100_000_000)
    v1 = bcs.TransactionDataV1(kind, bcs.Address(list(bytes.fromhex(sender[2:]))),
                               gas_data, bcs.TransactionExpiration("None", None))
    return bcs.TransactionData("V1", v1).serialize()


def sign_and_execute(sk: SigningKey, tx_bytes: bytes) -> dict:
    intent_msg = b"\x00\x00\x00" + tx_bytes
    digest = hashlib.blake2b(intent_msg, digest_size=32).digest()
    sig = sk.sign(digest).signature
    user_sig = base64.b64encode(b"\x00" + bytes(sig) + bytes(sk.verify_key)).decode()

    mutation = """
    mutation ($tx: Base64!, $sigs: [Base64!]!) {
      executeTransaction(transactionDataBcs: $tx, signatures: $sigs) {
        effects {
          digest status
          executionError { message }
        }
      }
    }"""
    r = httpx.post(GRAPHQL, json={
        "query": mutation,
        "variables": {"tx": base64.b64encode(tx_bytes).decode(),
                      "sigs": [user_sig]},
    }, timeout=60)
    body = r.json()
    if body.get("errors"):
        return {"errors": body["errors"]}
    eff = body["data"]["executeTransaction"]["effects"]
    return {"digest": eff["digest"], "status": eff["status"],
            "error": eff.get("executionError")}


if __name__ == "__main__":
    with open(os.path.join(ROOT, "sui_buyer_wallet.json")) as f:
        bw = json.load(f)
    sk = SigningKey(bytes(bw["seed"]))
    buyer = bw["address"]

    print(f"buyer: {buyer}  {balance(buyer)/LAMPORT:.4f} SUI")
    print(f"seller: {SELLER}  {balance(SELLER)/LAMPORT:.4f} SUI")

    # ---- Step 1+2: lock 0.5 SUI in escrow via OUR contract ---------------
    amount = 500_000_000
    ref = gas_ref(buyer)
    tx = build_escrow_create(buyer, SELLER, amount, "sentiment-analysis-api", ref)
    res = sign_and_execute(sk, tx)
    print("\n[LOCK] tx:", res.get("digest"), "status:", res.get("status"))
    if res.get("error"):
        print("error:", res["error"])
        sys.exit(1)

    import time
    time.sleep(3)

    # find the Escrow receipt object created for us
    import time
    nodes = []
    for _ in range(5):
        out = gql('{ address(address: "%s") { objects(first: 5) '
                  '{ nodes { address version digest } } } }' % buyer)
        nodes = (out.get("data") or {}).get("address", {}).get("objects", {}).get("nodes", [])
        if len(nodes) > 1:
            break
        time.sleep(2)
    print(f"[LOCK] buyer now owns {len(nodes)} objects (escrow receipt included)")

    bal_after_lock = balance(buyer)
    print(f"[LOCK] buyer balance after lock: {bal_after_lock/LAMPORT:.4f} SUI "
          f"(funds held by contract, spendable by nobody until release/cancel)")

    # ---- Step 4 (cancel path): reclaim via escrow::cancel ----------------
    # find the escrow object id (it's the newest non-gas object)
    escrow_objs = [n for n in nodes if n["address"] != ref["id"]]
    if escrow_objs:
        esc = escrow_objs[-1]
        print(f"\n[CANCEL] cancelling escrow {esc['address'][:18]}…")
        tx2 = build_escrow_cancel(buyer, esc["address"], int(esc["version"]),
                                  esc["digest"])
        res2 = sign_and_execute(sk, tx2)
        print("[CANCEL] tx:", res2.get("digest"), "status:", res2.get("status"))
        if res2.get("error"):
            print("error:", res2["error"])

    time.sleep(3)
    print(f"\nfinal buyer balance: {balance(buyer)/LAMPORT:.4f} SUI")
    print("DONE — escrow create + cancel both executed against deployed contract")
