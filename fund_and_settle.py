"""Autonomous funding + first REAL on-chain settlement.

Tries requestAirdrop until the IP quota resets. The moment SOL lands:
  1. builds + signs a real transfer
  2. sends it via RPC
  3. confirms on-chain
  4. verifies via getTransaction (amount + recipient)
Exit codes: 0=funded & settled, 2=still rate-limited, 1=error.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import Message
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.hash import Hash
from solders.instruction import Instruction, AccountMeta

RPCS = ["https://api.devnet.solana.com", "https://api.testnet.solana.com"]
ROOT = os.path.dirname(os.path.abspath(__file__))
MEMO_PROG = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"


def rpc(method, params, rpc_url=None):
    url = rpc_url or RPCS[0]
    return httpx.post(url, json={"jsonrpc": "2.0", "id": 1,
                                 "method": method, "params": params},
                      timeout=25).json()


def load_kp():
    with open(os.path.join(ROOT, "solana_agent_wallet.json")) as f:
        return Keypair.from_bytes(bytes(json.load(f)["secret"]))


def try_airdrop(pubkey: str) -> dict:
    """Try each public RPC until one dispenses funds."""
    reasons = []
    for url in RPCS:
        out = rpc("requestAirdrop", [pubkey, 500_000_000], rpc_url=url)  # 0.5 SOL
        if "result" in out:
            for _ in range(20):
                st = rpc("getSignatureStatuses", [[out["result"]]], rpc_url=url)
                v = st.get("result", {}).get("value", [None])[0]
                if v and v.get("confirmationStatus") in ("confirmed", "finalized"):
                    return {"ok": True, "sig": out["result"], "rpc": url}
                if v and v.get("err"):
                    break
                time.sleep(2)
            reasons.append(f"{url}: confirmation timeout")
        else:
            reasons.append(f"{url}: {out.get('error', {}).get('message', '?')[:80]}")
    return {"ok": False, "reason": "; ".join(reasons)}


def main() -> int:
    kp = load_kp()
    addr = str(kp.pubkey())
    bal0 = rpc("getBalance", [addr]).get("result", {}).get("value", 0)
    print(f"wallet {addr} balance {bal0} lamports")

    if bal0 == 0:
        print("attempting airdrop…")
        drop = try_airdrop(addr)
        if not drop["ok"]:
            print(f"NOT FUNDED: {drop['reason']}")
            return 2
        print(f"FUNDED via airdrop sig {drop['sig'][:16]}…")

    bal = rpc("getBalance", [addr]).get("result", {}).get("value", 0)
    if bal < 5000:
        print("insufficient balance even after attempt")
        return 2
    print(f"balance now {bal} lamports — executing REAL settlement")

    # ---- the actual payment: wallet -> its own vendor sub-wallet ----------
    vendor = Keypair()  # fresh recipient (vendor address)
    to = vendor.pubkey()
    amt = 1_000_000  # 0.001 SOL — one paid API call

    bh = Hash.from_string(rpc("getLatestBlockhash", [])["result"]["value"]["blockhash"])
    ix_t = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=to, lamports=amt))
    ix_m = Instruction(
        program_id=Pubkey.from_string(MEMO_PROG),
        accounts=[AccountMeta(kp.pubkey(), True, False)],
        data=b"x402-payment-/v1/block-stats")
    msg = Message.new_with_blockhash([ix_t, ix_m], kp.pubkey(), bh)
    tx = Transaction([kp], msg, bh)

    sent = rpc("sendTransaction", [base64.b64encode(bytes(tx)).decode(),
                                   {"encoding": "base64"}])
    if "error" in sent:
        print(f"send failed: {sent['error']}")
        return 1
    sig = sent["result"]
    print(f"sent tx {sig[:20]}…")

    for _ in range(30):
        st = rpc("getSignatureStatuses", [[sig]])
        v = st.get("result", {}).get("value", [None])[0]
        if v and v.get("confirmationStatus") in ("confirmed", "finalized"):
            break
        time.sleep(1)
    else:
        print("confirmation timeout")
        return 1
    if v.get("err"):
        print(f"tx failed on chain: {v['err']}")
        return 1
    print(f"CONFIRMED at slot {v['slot']}")

    # server-side style verification from chain state
    detail = rpc("getTransaction", [sig, "json", "confirmed"]).get("result", {})
    pre, post = detail["meta"]["preBalances"], detail["meta"]["postBalances"]
    keys = [str(Pubkey.from_string(k)) for k in detail["transaction"]["message"]["accountKeys"]]
    recv_idx = keys.index(str(to))
    received = post[recv_idx] - pre[recv_idx]
    ok = received >= amt
    print(f"on-chain verify: recipient got {received} lamports "
          f"(expected ≥{amt}) -> {'VERIFIED ✓' if ok else 'FAIL ✗'}")

    print("\nREAL ON-CHAIN SETTLEMENT COMPLETE"
          if ok else "\nverification mismatch")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
