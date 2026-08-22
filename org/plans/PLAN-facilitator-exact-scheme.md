# PLAN — DIR-011: Migrate Sui rail to x402 v2 exact scheme (facilitator-based)

**Directive:** DIR-011 | **Owner:** builder | **Planned:** planner, 2026-08-22 shift
**Status:** ready
**Why:** Custom `X-SUI-TX-DIGEST` dialect makes us unlistable on Agent402 / discovery-index /
PayAPI and unreachable by standard x402 clients. The hosted facilitator
(https://sui-facilitator.onrender.com, `/supported` verified live this shift) implements the
spec `exact` scheme on `sui:testnet` non-custodially, zero fees. This migration is the
prerequisite DIR-003 listings are blocked on.

## Reference facts (verified)
- Facilitator API: `POST /verify` and `POST /settle`, body
  `{x402Version, paymentPayload, paymentRequirements}` → HTTP 200 with
  `{isValid|success, invalidReason|errorReason, payer, transaction?, amount?}`.
- Wire types (`src/x402.ts` of DrVelvetFog/sui-x402-facilitator, cloned & read):
  - PaymentRequirements: `{scheme:"exact", network:"sui:testnet", amount:<atomic-units-string>,
    asset:<coin-type>, payTo:<sui-address>, maxTimeoutSeconds}`
  - PaymentPayload: `{x402Version:2, accepted:<requirements>, payload:{signature:<b64>,
    transaction:<b64 tx bytes>}}`
  - Challenge: 402 with base64 `PAYMENT-REQUIRED` header; retry carries base64
    `PAYMENT-SIGNATURE` header; success returns `PAYMENT-RESPONSE` settlement digest.
- Testnet USDC coin type: `0xa1ec7fc00a6f40db9693ad1415d0c193ad3906494428cf252621037bd7117e29::usdc::USDC` (6 decimals).
- Current server: `sui_market_server.py` :8604, legacy header `X-SUI-TX-DIGEST`, prices in MIST.

## GOAL
`sui_market_server.py` accepts the standard x402 v2 `PAYMENT-SIGNATURE` flow (settled via the
hosted facilitator in testnet USDC) while keeping the legacy `X-SUI-TX-DIGEST` path working.
Prices move to catalog-USDC parity: sentiment 15000, entity-extract 30000, summarize 75000
atomic units ($0.015 / $0.030 / $0.075).

## STEPS (each one command or one edit; total <10 min)
1. `cd ~/x402-agent-service && git pull --ff-only` — start from HEAD.
2. Create `sui_x402_v2.py` (new file, ~120 lines):
   - `b64d(s)` / `b64e(o)` helpers (urlsafe base64, JSON in/out).
   - `TESTNET_USDC`, `FACIL = "https://sui-facilitator.onrender.com"`.
   - `requirements(endpoint)` → PaymentRequirements dict using price table
     {"/v1/sentiment":15000, "/v1/entity-extract":30000, "/v1/summarize":75000},
     `payTo` = seller address from `sui_seller_wallet.json`, `maxTimeoutSeconds: 600`.
   - `challenge_402(reqs)` → JSONResponse(402) with `PAYMENT-REQUIRED` b64 header
     `{x402Version:2, error:"payment_required", accepts:[reqs]}` (keep existing JSON body too,
     for human debugging).
   - `settle_via_facilitator(payload_b64, reqs)` → decode `PAYMENT-SIGNATURE`, POST `/verify`;
     if `isValid` POST `/settle`; return `(ok, digest_or_reason)`. Never broadcast anything
     ourselves; never touch keys.
3. Edit `sui_market_server.py` `paid()`: BEFORE the legacy branch, if header
   `PAYMENT-SIGNATURE` present → call `settle_via_facilitator(...)`; on ok, serve + add
   `"scheme":"x402-v2-exact"` to receipt; else 402 with reason. Legacy `X-SUI-TX-DIGEST`
   branch stays untouched below it.
4. Update `/bazaar` entries: add per-endpoint `"accepts":[<requirements>]` so standard
   clients see terms without a challenge round-trip.
5. `.venv/bin/python -m py_compile sui_x402_v2.py sui_market_server.py`
6. `git add -A && git commit -m "builder: DIR-011 x402-v2 exact scheme on Sui rail (facilitator-settled, dual-dialect)" && git push`

## VERIFY (exact commands + expected output)
- `curl -si https://sui-facilitator.onrender.com/supported` → contains `"sui:testnet"` (already re-verified this shift).
- Restart server: `pkill -f sui_market_server.py; sleep 1; nohup .venv/bin/python sui_market_server.py > /tmp/sui8610.log 2>&1 &`
- `curl -si -X POST localhost:8604/v1/sentiment -d 'text=hello' | grep -i payment-required`
  → a `PAYMENT-REQUIRED:` base64 header line; decoding it yields `accepts[0].asset == "...::usdc::USDC"`, `amount == "15000"`.
- Free conformance probe (no funds needed): send a deliberately corrupt payload —
  `.venv/bin/python -c` snippet calling `settle_via_facilitator(b64("not-json"), requirements("/v1/sentiment"))`
  → expect `(False, ...)` and facilitator returning HTTP 200 `{"isValid": false, ...}` (semantic failure, never a crash).
- `bash ci.sh` → all stages pass (legacy-dialect tests must still pass).
- `curl -s localhost:8604/bazaar` → 3 endpoints, each with `accepts`.

## ROLLBACK
- `git revert <commit> && pkill -f sui_market_server.py && nohup .venv/bin/python sui_market_server.py > /tmp/sui8610.log 2>&1 &`
- Legacy path was never modified, so pre-migration behavior is restored exactly.

## Execution 2026-08-22 (builder shift) — status=done

Code (sui_x402_v2.py + sui_market_server.py integration) was found staged from the prior
shift; this shift completed compile checks, live verification, and org bookkeeping.
All VERIFY commands run for real:

1. `.venv/bin/python -m py_compile sui_x402_v2.py sui_market_server.py` → exit 0.
2. `curl -s https://sui-facilitator.onrender.com/supported` →
   `{"kinds":[{"x402Version":2,"scheme":"exact","network":"sui:testnet","extra":{"usdc":"0xa1ec...7e29::usdc::USDC","decimals":6}}, ...]}` ✓
3. Server restarted on :8604; `/health` → `{"status":"ok","pay_to":"0x8b355339...78c924a","settlement":"sui-devnet"}`.
   Note: plan's VERIFY said `-X POST`, but routes are GET (`@app.get("/{path:path}")`);
   GET used instead: `curl -si "localhost:8604/v1/sentiment?text=hello"` →
   `HTTP/1.1 402 Payment Required` + `payment-required:` base64 header.
4. Decoded PAYMENT-REQUIRED header:
   `x402Version: 2 | asset: 0xa1ec7fc00a6f40db9693ad1415d0c193ad3906494428cf252621037bd7117e29::usdc::USDC | amount: "15000" | scheme: exact | network: sui:testnet` ✓
5. Free conformance probes (no funds):
   - garbage payload → `(False, 'verify failed: invalid_x402_version')`
   - well-formed fake tx → facilitator HTTP **200** `{'isValid': False, 'invalidReason': 'invalid_transaction_state'}`,
     helper returned `(False, 'verify failed: invalid_transaction_state')` — semantic reject, no crash ✓
6. `/bazaar` → all 3 endpoints each carry `"accepts"` with exact-scheme requirements at
   15000 / 30000 / 75000 atomic units, payTo = seller address ✓
7. `bash ci.sh` → ALL 7 INTEGRATION STAGES PASSED ("ALL INTEGRATION STAGES PASSED",
   economy check BALANCED, MCP smoke tests green) — legacy dialect intact ✓

ROLLBACK not needed. Live settled purchase intentionally NOT attempted (per NOTES: Circle
faucet human-gated); structural migration is fully verified free of charge.

## ESTIMATED REVENUE IMPACT
Indirect but structural: unblocks DIR-003 listings (Agent402 = one POST, discovery-index =
one issue, PayAPI free listing) and makes us callable by stock x402 clients — i.e., converts
marketing spend into reachable shelf space. Direct sales unchanged until a buyer arrives;
target remains $20/day via the repriced catalog once distribution lands.

## NOTES / BOUNDARIES
- Do NOT attempt a live settled purchase here: testnet USDC comes from Circle's faucet
  (human-gated, likely network-blocked). Structural migration is fully verifiable for free
  (steps above); live-settle proof belongs to a later directive once a funded tester exists.
- No private keys are read, moved, or transmitted; facilitator is non-custodial by design.
