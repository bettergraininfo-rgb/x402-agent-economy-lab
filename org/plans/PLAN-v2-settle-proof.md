# PLAN — DIR-020: One real x402 v2 exact-scheme SETTLE on Sui testnet

**Directive:** DIR-020 | **Owner:** builder | **Planned:** planner, 2026-08-22 ~12:30 MDT shift
**Status:** ready
**Why:** Listings currently cite a *challenge* (402 shape), not a proven *settle*. One real
facilitator `/settle` broadcast on `sui:testnet` turns every listing claim into "settle path
proven on-chain".

## Reference facts (verified this shift)
- Facilitator `https://sui-x402-facilitator.onrender.com` `/supported` → exact / sui:testnet,
  asset-agnostic ("enforces whatever coin type PaymentRequirements.asset names"; its own e2e
  includes SUI-denominated settlements — PROOF.md digests 4WZzq5jW…, 9SUDSAuS…).
- Testnet USDC has NO agent-reachable faucet (Circle = human-gated) ⇒ proof runs
  **SUI-denominated**: asset `0x2::sui::SUI`, amount in MIST. Same scheme, same network,
  same facilitator endpoints our server uses — the settle PATH is what gets proven.
- Testnet faucet IS reachable from this host (probe 12:2x MDT: HTTP 429 "wait 5s" on a dummy
  address = alive + rate-limit only). Testnet GraphQL live (`chainIdentifier` OK).
- Reusable code already in repo:
  - `sui_a2a_pay.py`: `build_split_transfer_tx()` + `sign()` → exactly `(tx_b64, sig_b64)`
    (flag-prefixed ed25519, blake2b intent digest) the facilitator expects.
  - `sui_x402_v2.py`: `settle_via_facilitator(payload_b64, reqs)` → verify→settle relay.
- Seller address from `sui_seller_wallet.json` is network-independent (address derivation);
  it can receive testnet funds without any key access.

## GOAL
A fresh buyer wallet pays our seller address on `sui:testnet` through the full standard flow:
402-shaped requirements → payer-signed tx → facilitator `/verify` (isValid:true) → facilitator
`/settle` (success + transaction digest) → balance delta confirmed on-chain. Evidence recorded;
listings updated to cite it.

## STEPS (each one command or one edit; total <10 min)
1. `cd ~/x402-agent-service && git pull --ff-only` — start from HEAD.
2. Probe faucet budget: `curl -s --max-time 15 -X POST https://faucet.testnet.sui.io/v2/gas -H 'Content-Type: application/json' -d '{"FixedAmountRequest":{"recipient":"<fresh-address>"}}'`
   If persistent 5xx/blocked → STOP local route, rerun steps 3–6 inside a GitHub Actions
   runner (open internet); do not burn the shift retrying locally.
3. Create `sui_v2_buyer.py` (~90 lines): constants `GRAPHQL="https://graphql.testnet.sui.io/graphql"`,
   `FAUCET="https://faucet.testnet.sui.io/v2/gas"`; import `build_split_transfer_tx`, `sign`
   from `sui_a2a_pay` and `b64e`/`settle_via_facilitator` from `sui_x402_v2`. main():
   a. create/load `sui_testnet_buyer_wallet.json` (reuse `suisettle.create_wallet` pattern).
   b. if balance==0 → faucet request; sleep 5; re-check (retry ≤3×, honoring 60-min cooldown
      by exiting code 2 cleanly if still unfunded).
   c. `reqs = {"scheme":"exact","network":"sui:testnet","amount":"15000000","asset":"0x2::sui::SUI","payTo":<seller>,"maxTimeoutSeconds":600}`
      (15000000 MIST = 0.015 SUI ≈ sentiment price parity).
   d. `ref = gas_ref(buyer)`; `tx_b64, sig = sign(sk, build_split_transfer_tx(buyer, seller, 15000000, ref))`.
   e. `payload = {"x402Version":2,"accepted":reqs,"payload":{"signature":sig,"transaction":tx_b64}}`;
      `ok, result = settle_via_facilitator(b64e(payload), reqs)`; print both.
4. `.venv/bin/python -m py_compile sui_v2_buyer.py && .venv/bin/python sui_v2_buyer.py`
   Expect `ok=True`, result `<digest> payer=0x…`.
5. Confirm on-chain via testnet GraphQL `balanceChanges` for that digest (or print
   `https://testnet.suivision.xyz/txblock/<digest>` URL) — seller credited ≥15000000 MIST.
6. Record evidence under `## Execution` below; append one line to org/decisions.log;
   `git add sui_v2_buyer.py && git commit -m "builder: DIR-020 real x402 v2 exact-scheme settle proof on sui:testnet" && git push`.

## VERIFY (exact commands + expected output)
- Step 4 stdout contains `(True, '<64-char digest> payer=0x')` — facilitator settled, not simulated.
- Balance check: seller-side GraphQL query for the digest returns a credit of ≥15000000 MIST
  to the seller address; buyer debited amount+gas.
- Replay guard (free): re-running step 4 with the SAME signed payload must FAIL with an
  invalid_transaction_state-class reason (double-settle impossible). One extra run proves it.
- `bash ci.sh` still all-green (no server code touched).

## ROLLBACK
- Nothing to revert: new standalone script only; :8604/:8610 servers, ledger, and wallets untouched.
- If faucet got funded but settle failed: funds sit in `sui_testnet_buyer_wallet.json`
  (gitignored — confirm before committing) as dust; no action needed.

## ESTIMATED REVENUE IMPACT
Indirect but listing-critical: converts DIR-003/017 listing copy from "accepts challenges" to
"settlement proven end-to-end on sui:testnet via non-custodial facilitator" — removes the last
honesty caveat from channel (b). USDC-denominated settle remains gated on dust acquisition
(DIR-016 pattern); optional accelerator: request testnet-USDC dust from DrVelvetFog via the
already-open thread #1 (they run the facilitator and demonstrably hold testnet USDC).

## NOTES / BOUNDARIES
- Buyer key is a FRESH throwaway wallet created by the script; never read/move existing
  wallet JSON private keys.
- Do not modify `sui_x402_v2.py` V2_PRICES/TESTNET_USDC — the published catalog stays USDC;
  this proof only exercises the settle path with a facilitator-supported alternative asset.
