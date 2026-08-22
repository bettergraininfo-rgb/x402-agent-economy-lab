"""Agent-to-agent payment on Sui devnet — REAL signed on-chain transaction.

Uses pysui's BCS types to build a proper ProgrammableTransaction:
  SplitCoin(gas, [1 SUI]) -> TransferObjects([split], seller)
Signs with the buyer's ed25519 key (blake2b intent digest), submits via the
GraphQL executeTransaction mutation, verifies via GraphQL + balance delta.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

import httpx
from nacl.signing import SigningKey

from pysui.sui.sui_bcs import bcs

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHQL = "https://graphql.devnet.sui.io/graphql"
LAMPORT = 1_000_000_000


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


def build_split_transfer_tx(sender: str, recipient: str, amount: int, ref: dict) -> bytes:
    """SplitCoins(gas, amount); TransferObjects([split], recipient)."""
    inputs = [
        # 1: pure u64 amount
        bcs.CallArg("Pure", list(amount.to_bytes(8, "little"))),
        # 2: recipient address
        bcs.CallArg("Pure", list(bytes.fromhex(recipient[2:]))),
    ]
    commands = [
        # SplitCoin on the GAS object itself (implicit, no input needed)
        bcs.Command("SplitCoin", bcs.SplitCoin(
            FromCoin=bcs.Argument("GasCoin"),
            Amount=[bcs.Argument("Input", 0)])),
        bcs.Command("TransferObjects", bcs.TransferObjects(
            Objects=[bcs.Argument("Result", 0)],
            Address=bcs.Argument("Input", 1))),
    ]
    pt = bcs.ProgrammableTransaction(inputs, commands)
    kind = bcs.TransactionKind("ProgrammableTransaction", pt)
    gas_data = bcs.GasData(
        [bcs.ObjectReference(bcs.Address(list(bytes.fromhex(ref["id"][2:]))),
                             ref["version"],
                             bcs.Digest(list(__import__("base58").b58decode(ref["digest"]))))],
        bcs.Address(list(bytes.fromhex(sender[2:]))), 1000, 50_000_000)
    v1 = bcs.TransactionDataV1(kind, bcs.Address(list(bytes.fromhex(sender[2:]))), gas_data,
                               bcs.TransactionExpiration("None", None))
    data = bcs.TransactionData("V1", v1)
    return data.serialize()


def sign(sk: SigningKey, tx_bytes: bytes) -> tuple[str, str]:
    intent_msg = b"\x00\x00\x00" + tx_bytes   # sui::default intent
    digest = hashlib.blake2b(intent_msg, digest_size=32).digest()
    sig = sk.sign(digest).signature
    user_sig = base64.b64encode(b"\x00" + bytes(sig) + bytes(sk.verify_key)).decode()
    tx_b64 = base64.b64encode(tx_bytes).decode()
    return tx_b64, user_sig


def execute(tx_b64: str, user_sig: str) -> dict:
    mutation = """
    mutation ($tx: Base64!, $sigs: [Base64!]!) {
      executeTransaction(transactionDataBcs: $tx, signatures: $sigs) {
        effects {
          digest status
          executionError { message }
          balanceChanges { nodes { owner { address } amount } }
        }
      }
    }"""
    r = httpx.post(GRAPHQL, json={
        "query": mutation,
        "variables": {"tx": tx_b64, "sigs": [user_sig]},
    }, timeout=60)
    return r.json()


if __name__ == "__main__":
    with open(os.path.join(ROOT, "sui_buyer_wallet.json")) as f:
        bw = json.load(f)
    sk = SigningKey(bytes(bw["seed"]))
    buyer = bw["address"]
    with open(os.path.join(ROOT, "sui_seller_wallet.json")) as f:
        seller = json.load(f)["address"]

    print("buyer :", buyer, f"{balance(buyer)/LAMPORT} SUI")
    print("seller:", seller, f"{balance(seller)/LAMPORT} SUI")

    ref = gas_ref(buyer)
    print("gas object:", ref["id"][:18], "v", ref["version"])

    amount = LAMPORT  # 1 SUI service fee
    tx_bytes = build_split_transfer_tx(buyer, seller, amount, ref)
    print("tx built,", len(tx_bytes), "bytes")

    tx_b64, user_sig = sign(sk, tx_bytes)
    result = execute(tx_b64, user_sig)

    if "errors" in result:
        print("EXECUTION ERRORS:", json.dumps(result["errors"])[:400])
    else:
        eff = result["data"]["executeTransaction"]["effects"]
        print("TX DIGEST:", eff["digest"])
        print("status:", eff["status"], eff.get("executionError"))
        changes = (eff.get("balanceChanges") or {}).get("nodes", [])
        for ch in changes:
            owner = (ch.get("owner") or {}).get("address")
            print(f"  {owner}: {int(ch['amount'])/LAMPORT:+} SUI")
