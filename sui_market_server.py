"""Real-settlement x402 market on Sui devnet.

The 402 challenge names a pay_to address + MIST amount. The buyer agent
executes a REAL signed Sui transfer, then retries with the tx digest. The
server verifies ON-CHAIN (GraphQL): status SUCCESS, funds landed on pay_to,
amount >= price, digest never seen before (replay protection). Only then
is the service served.

This replaces MockFacilitator with the actual Sui ledger.
"""

from __future__ import annotations

import base64
import json

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import sui_x402_v2 as v2

GRAPHQL = "https://graphql.devnet.sui.io/graphql"
PAY_TO = "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a"
LAMPORT = 1_000_000_000

app = FastAPI(title="sui-x402-market", version="1.0.0")

SERVICES = {
    "/v1/sentiment":      {"price": 50_000_000, "fn": None},
    "/v1/entity-extract": {"price": 80_000_000, "fn": None},
    "/v1/summarize":      {"price": 120_000_000, "fn": None},
}


def svc_sentiment(text: str) -> dict:
    pos = {"good", "great", "love", "amazing", "win", "gain", "profit"}
    neg = {"bad", "terrible", "awful", "hate", "worst", "crash", "scam"}
    words = [w.strip(".,!?;:").lower() for w in text.split()]
    p, n = sum(w in pos for w in words), sum(w in neg for w in words)
    label = "positive" if p > n else "negative" if n > p else "neutral"
    return {"label": label,
            "score": round(min(1.0, .4 + .2 * abs(p - n)) * (1 if p > n else -1 if n > p else 0), 2)}


def svc_entities(text: str) -> dict:
    known = {"Coinbase", "Base", "Virtuals", "Solana", "Ethereum", "Sui", "Mysten"}
    caps = {w.strip(".,!?;:") for w in text.split() if w[:1].isupper()}
    return {"organizations": sorted(caps & known),
            "proper_nouns": sorted(caps - known)}


def svc_summarize(text: str) -> dict:
    import re
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if len(sents) <= 2:
        return {"summary": text[:280], "sentences_in": len(sents), "sentences_out": len(sents)}
    freq: dict[str, int] = {}
    for w in re.findall(r"[a-z']+", text.lower()):
        if len(w) > 3:
            freq[w] = freq.get(w, 0) + 1
    def score(s):
        ws = re.findall(r"[a-z']+", s.lower())
        return sum(freq.get(w, 0) for w in ws) / max(1, len(ws))
    keep = sorted(range(len(sents)), key=lambda i: -score(sents[i]))[: max(1, len(sents)//3)]
    return {"summary": " ".join(sents[i] for i in sorted(keep)),
            "sentences_in": len(sents), "sentences_out": len(keep)}


SERVICES["/v1/sentiment"]["fn"] = svc_sentiment
SERVICES["/v1/entity-extract"]["fn"] = svc_entities
SERVICES["/v1/summarize"]["fn"] = svc_summarize

_seen_digests: set[str] = set()
ledger: list[dict] = []


def gql(query: str) -> dict:
    return httpx.post(GRAPHQL, json={"query": query}, timeout=30).json()


def verify_onchain(digest: str, min_amount: int, attempts: int = 5) -> tuple[bool, str]:
    """Check the ledger: tx succeeded and paid pay_to at least min_amount.
    Retries while indexing catches up."""
    if digest in _seen_digests:
        return False, "digest replayed"
    import time
    tb = None
    for _ in range(attempts):
        out = gql("""
        { transaction(digest: "%s") {
            effects { status executionError { message }
              balanceChanges { nodes { owner { address } amount } } } } }""" % digest)
        tb = (out.get("data") or {}).get("transaction")
        if tb:
            break
        time.sleep(1.5)  # GraphQL indexer lag behind execution
    if not tb:
        return False, "transaction not found on chain"
    eff = tb["effects"]
    if eff["status"] != "SUCCESS":
        return False, f"tx status {eff['status']}"
    paid = 0
    for ch in eff["balanceChanges"]["nodes"]:
        owner = (ch.get("owner") or {}).get("address")
        if owner and owner.lower() == PAY_TO.lower():
            paid += abs(int(ch["amount"]))
    if paid < min_amount:
        return False, f"paid {paid} MIST, required {min_amount}"
    _seen_digests.add(digest)
    return True, f"verified {paid} MIST received"


@app.get("/")
def root():
    """Origin manifest for x402 index crawlers (Agent402 probes origin root)."""
    return {
        "service": "x402-agent-economy-lab NLP micro-services",
        "description": ("Machine-payable NLP APIs: sentiment, entity-extract, "
                        "summarize. Pay per call in USDC via x402 (v2 exact scheme, "
                        "sui:testnet) — unauthenticated request returns the 402 "
                        "challenge with accepts[] payment requirements."),
        "catalog": "/bazaar",
        "health": "/health",
        "stats": "/stats",
        "repo": "https://github.com/bettergraininfo-rgb/x402-agent-economy-lab",
        "endpoints": [ep for ep in SERVICES],
    }


@app.get("/.well-known/x402")
def well_known_x402(request: Request):
    """Agent402 service manifest (spec: agent402-service-manifest/1)."""
    base = str(request.base_url).rstrip("/")
    return {
        "spec": "agent402-service-manifest/1",
        "version": 1,
        "resources": [f"{base}{ep}" for ep in SERVICES],
        "payment": "x402 v2 exact scheme (sui:testnet USDC) - unauthenticated "
                   "request returns HTTP 402 with accepts[] requirements",
    }


@app.get("/health")
def health():
    return {"status": "ok", "pay_to": PAY_TO, "settlement": "sui-devnet"}


@app.get("/bazaar")
def bazaar():
    return {"services": [
        {"endpoint": ep, "price_sui": cfg["price"] / LAMPORT,
         **({"accepts": [v2.requirements(ep)]} if ep in v2.V2_PRICES else {})}
        for ep, cfg in SERVICES.items()
    ]}


@app.get("/stats")
def stats():
    return {"revenue_mist": sum(e["amount"] for e in ledger),
            "sales": len(ledger),
            "by_service": _by_svc()}


def _by_svc():
    out: dict[str, int] = {}
    for e in ledger:
        out[e["service"]] = out.get(e["service"], 0) + e["amount"]
    return out


@app.get("/{path:path}")
def paid(request: Request, path: str, text: str = ""):
    endpoint = "/" + path
    cfg = SERVICES.get(endpoint)
    if not cfg:
        return JSONResponse({"error": "unknown service"}, status_code=404)
    if not text:
        return JSONResponse({"error": "missing ?text="}, status_code=400)

    digest = request.headers.get("X-SUI-TX-DIGEST")
    sig = request.headers.get("PAYMENT-SIGNATURE")

    # --- x402 v2 exact scheme (standard dialect, facilitator-settled) ---
    if sig:
        reqs = v2.requirements(endpoint)
        ok, reason = v2.settle_via_facilitator(sig.strip(), reqs)
        if not ok:
            return JSONResponse(
                {"error": "payment rejected", "reason": reason,
                 "scheme": "x402-v2-exact"},
                status_code=402)
        receipt = {"tx": reason, "service": endpoint,
                   "amount": int(reqs["amount"]),
                   "settlement": "facilitator", "scheme": "x402-v2-exact"}
        ledger.append(receipt)
        return JSONResponse(content={**cfg["fn"](text), "_receipt": receipt})

    if not digest:
        reqs = v2.requirements(endpoint)
        challenge = {
            "x402Version": 2,
            "accepts": [reqs],
            "error": "Payment Required",
            "scheme": "sui-transfer",
            "pay_to": PAY_TO,
            "amount_mist": cfg["price"],
            "network": "sui-devnet",
            "instructions": "Execute a SUI transfer of amount_mist to pay_to, "
                            "then retry with header X-SUI-TX-DIGEST: <digest> "
                            "(or use x402 v2 exact via PAYMENT-SIGNATURE)",
        }
        header_body = {"x402Version": 2, "error": "payment_required",
                       "accepts": [reqs]}
        return JSONResponse(status_code=402, content=challenge,
                            headers={"PAYMENT-REQUIRED": v2.b64e(header_body)})

    ok, reason = verify_onchain(digest.strip(), cfg["price"])
    if not ok:
        return JSONResponse({"error": "payment rejected", "reason": reason},
                            status_code=402)

    receipt = {"tx": digest, "service": endpoint, "amount": cfg["price"],
               "settlement": "on-chain"}
    ledger.append(receipt)
    return JSONResponse(content={**cfg["fn"](text), "_receipt": receipt})
