"""storefront.py — GitHub-Issue-based storefront for the agent economy business.

Why: this machine has no inbound network (tunnel ports blocked), but GitHub
is reachable by everyone. So the storefront lives where the customers are.

Flow:
  1. Buyer pays USDC on Base mainnet to the receiving wallet (see /health).
  2. Buyer opens a GitHub issue using the 'x402 Order' template:
     title: [x402-order] <endpoint>
     body includes: tx hash (0x...), endpoint name, input text.
  3. Operator/bot runs: python3 storefront.py poll
     - finds open issues labeled x402-order
     - verifies the tx ON-CHAIN (real USDC transfer, correct amount, fresh,
       unused) via revenue_server.verify_payment
     - fulfills the order, comments the JSON result, closes the issue,
       records the sale in org/revenue_ledger.json
     - invalid payments get a clear rejection comment and are closed.

Usage:
  python3 storefront.py poll          # process pending orders once
  python3 storefront.py stats         # lifetime revenue summary
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from revenue_server import SERVICES, RECIPIENT, _load_ledger, _record, _units, verify_payment  # noqa: E402
from bazaar import svc_batch, svc_entities, svc_report, svc_sentiment, svc_summarize  # noqa: E402

REPO = "bettergraininfo-rgb/x402-agent-economy-lab"
LABEL = "x402-order"
LABEL_DONE = "fulfilled"


def gh(*args: str) -> str:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}… failed: {out.stderr.strip()[:300]}")
    return out.stdout


def parse_order(body: str) -> dict | None:
    """Extract tx hash, endpoint, and input text from an order issue body."""
    tx = None
    m = re.search(r"\b(0x[a-fA-F0-9]{64})\b", body)
    if m:
        tx = m.group(1)
    endpoint = None
    m = re.search(r"endpoint\s*[:\-]\s*\`?(/?v1/[a-z\-]+)\`?", body, re.I)
    if m:
        endpoint = m.group(1)
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        endpoint = endpoint.rstrip("/").lower()
    text = ""
    m = re.search(r"(?:input|text)\s*[:\-]\s*(.+)", body, re.I | re.S)
    if m:
        text = m.group(1).strip()[:20000]
    return {"tx": tx, "endpoint": endpoint, "text": text}


def fulfill(endpoint: str, text: str) -> dict:
    if endpoint == "/v1/sentiment":
        return {"result": svc_sentiment(text)}
    if endpoint == "/v1/entity-extract":
        return {"result": svc_entities(text)}
    if endpoint == "/v1/summarize":
        return {"result": svc_summarize(text)}
    if endpoint == "/v1/report":
        return {"result": svc_report(text)}
    if endpoint == "/v1/batch":
        return {"result": svc_batch(text)}
    raise ValueError(f"unknown endpoint {endpoint}")


def poll() -> None:
    issues = json.loads(gh("issue", "list", "-R", REPO, "--label", LABEL,
                           "--state", "open", "--json", "number,title,body"))
    print(f"{len(issues)} open order(s)")
    for iss in issues:
        num = iss["number"]
        order = parse_order(iss.get("body") or "")
        try:
            if not order or not order["tx"] or order["endpoint"] not in SERVICES:
                gh("issue", "comment", str(num), "-R", REPO,
                   "--body", "❌ Order malformed. Required: a 0x… transaction hash of your "
                            f"USDC-on-Base payment and a valid endpoint ({', '.join(SERVICES)}).")
                gh("issue", "close", str(num), "-R", REPO)
                continue

            price = SERVICES[order["endpoint"]]["price"]
            ok, reason, amount = asyncio.run(verify_payment(order["tx"], _units(price)))
            if not ok:
                gh("issue", "comment", str(num), "-R", REPO,
                   "--body", f"❌ Payment could not be verified on-chain: **{reason}**.\n\n"
                             f"Expected: ≥ ${price} USDC transferred to `{RECIPIENT}` on Base mainnet.")
                gh("issue", "close", str(num), "-R", REPO)
                continue

            ledger = _load_ledger()
            if order["tx"] in ledger["txs"]:
                gh("issue", "comment", str(num), "-R", REPO,
                   "--body", "⚠️ This transaction was already used for another order (replay protection).")
                gh("issue", "close", str(num), "-R", REPO)
                continue

            paid = amount or price
            result = fulfill(order["endpoint"], order["text"])
            _record(order["tx"], order["endpoint"], paid)
            body = (
                f"✅ Payment verified on-chain: **${paid} USDC** (tx `{order['tx']}`).\n\n"
                f"```json\n{json.dumps(result, indent=2)[:40000]}\n```\n\n"
                f"Thank you for your purchase. — agent economy fulfillment bot"
            )
            gh("issue", "comment", str(num), "-R", REPO, "--body", body)
            gh("issue", "edit", str(num), "-R", REPO, "--add-label", LABEL_DONE)
            gh("issue", "close", str(num), "-R", REPO)
            print(f"#{num} FULFILLED {order['endpoint']} ${paid} tx={order['tx'][:18]}…")
        except Exception as e:  # never leave an order unprocessed silently
            print(f"#{num} ERROR {e}")


def stats() -> None:
    d = _load_ledger()
    print(json.dumps({
        "lifetime_usdc": d.get("lifetime_usdc", 0),
        "sales": d.get("sales", 0),
        "by_endpoint": d.get("by_endpoint", {}),
        "recipient": RECIPIENT,
    }, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "poll":
        poll()
    elif cmd == "stats":
        stats()
    else:
        print(__doc__)
