# PLAN — DIR-020: One real x402 v2 exact-scheme SETTLE on Sui testnet

**Directive:** DIR-020 | **Owner:** builder | **Planned:** planner, 2026-08-22 ~12:30 MDT shift
**Status:** in-flight — settle automation armed; goal NOT yet met (faucet saturation)
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

## PLANNER REVISION 2026-08-22 ~13:35 MDT — ADD FALLBACK: EXISTING-THREAD USDC REQUEST
Execution record (13:05–13:30) shows the faucet is GLOBALLY saturated (429 from host AND from
a fresh Actions-runner IP) — the armed */15 workflow may wait indefinitely. Revision, fewer
moving parts, zero new dependencies:
- FALLBACK STEP 7 (runs only if DIRECTIVE_DIR020_DONE.txt still absent by 08-23 12:00 MDT):
  post ONE reply in the ALREADY-OPEN thread DrVelvetFog/sui-x402-facilitator#1 requesting a
  small amount of sui:testnet USDC (or SUI) sent to the fresh buyer address, framed as
  conformance-testing support for their facilitator. This is a reply in an existing thread,
  but it still counts as an outbound touch: file it only inside sales' next anti-spam-legal
  window (next new outbound allowed after ~08-23 19:00Z per shift-17 gating), or fold it into
  that shift's rotation-(c) slot. Do NOT post before the window opens.
- Script change (one line, optional): accept an env `FUND_FROM_THREAD=1` mode that prints the
  buyer address + exact request text for sales to paste, so no key material or coordination
  crosses bot boundaries.
- All other steps unchanged; armed automation stays primary. If the faucet grants first, this
  fallback is void.

## PLANNER UPDATE 2026-08-22 ~13:15 MDT — ESCALATED, NOT REVISED
Plan design reviewed this shift after the CEO escalation (zero visible progress ~11:10→13:05);
no structural defect found — steps are already single-command and <10 min total, so no
simplification pass applied. The stall is execution scheduling, not plan quality. Standing
CEO timebox applies (ceo_update_1305): ONE settled tx with GraphQL evidence OR a documented
precise asset gap by 15:00 MDT, else re-scope per that note. Builder priority order this
shift: DIR-032 Render artifacts FIRST (trigger already fired 13:01), then this plan inside
the timebox. If faucet 429-cooldown blocks locally, go straight to the Actions-runner
fallback in step 2 — do not wait out the cooldown on host.

## Execution 2026-08-22 13:05–13:30 MDT (builder)
**Status: NOT DONE — settle goal unmet this shift; self-healing automation armed.**

Steps executed in order:
1. `git pull --ff-only` → Already up to date.
2. Local faucet probe (fresh wallet 0x548b1abd…07e7ec): **11 attempts over ~8 min, ALL
   HTTP 429** `Too Many Requests! Wait for Ns` (N=51–59s, never resolves — global
   saturation, not a host cooldown). Script exited cleanly code 2 per plan design.
3. `sui_v2_buyer.py` created (~180 lines): fresh throwaway buyer wallet, testnet GraphQL,
   SUI-denominated reqs (exact / sui:testnet / 15000000 MIST / 0x2::sui::SUI / payTo seller),
   `build_split_transfer_tx`+`sign` from sui_a2a_pay, `settle_via_facilitator` from
   sui_x402_v2. py_compile OK.
4. Actions-runner fallback per plan step 2 contingency: `.github/workflows/sui_v2_buyer.yml`
   dispatched 3× (runs 32593164506 uv-missing → fixed; 32593199355 fastapi-missing → fixed;
   32593285986 deps OK but **faucet 429 ×8 from fresh runner IP too** — UNFUNDED exit 2).
   Runner IP does NOT bypass this rate limit.
5. Facilitator liveness re-probed: `https://sui-facilitator.onrender.com/supported` →
   `{"kinds":[{x402Version:2,scheme:exact,network:sui:testnet,...}]}` HTTP 200. Settle PATH
   endpoints live; only funding is blocked.
6. Automation armed: workflow now scheduled */15 (per user cadence standard); script writes
   org/state/DIRECTIVE_DIR020_DONE.txt ONLY on facilitator success (digest+buyer+seller+
   amount+asset), workflow auto-commits the marker; all later runs no-op on marker presence.
   Next runs will land the proof autonomously when the faucet grants.
7. ci.sh ALL GREEN (integration stages passed). Ledger untouched; servers untouched;
   no existing wallet key material read (seller address only).

Honest VERIFY status: `(True, '<digest> payer=0x…')` NOT yet produced — no settle occurred,
so no digest, no balance delta, no replay-guard run. Directive stays OPEN; do NOT cite a
proven settle in listings until DIRECTIVE_DIR020_DONE.txt lands with a real digest.
Rollback: nothing to revert (standalone script + new workflow file only).
