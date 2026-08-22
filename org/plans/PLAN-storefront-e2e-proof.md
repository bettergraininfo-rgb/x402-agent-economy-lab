# PLAN — DIR-012: Prove one live end-to-end storefront order (before any outreach cites it)

**Directive:** DIR-012 | **Owner:** builder | **Planned:** planner, 2026-08-22 shift
**Status:** ready (staged — see HARD CONSTRAINT)
**CEO bar:** "one live end-to-end storefront order before any outreach cites it."

## HARD CONSTRAINT (measured this shift, 10:30)
Receiving wallet `0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f` on Base mainnet holds
**0 ETH and 0 USDC** (verified via `eth_getBalance` + `eth_call balanceOf`, both `0x0`).
A genuinely live paid order therefore requires funding first. Funding is an operator
decision — this plan stages everything a bot can do for free, and gates the live step.

## GOAL
Prove the storefront pipeline end-to-end as far as possible at zero cost
(intake → parse → on-chain verify → reject/fulfill → comment → close → ledger), and leave a
single gated command that executes the real live self-order the moment the wallet is funded.

## PHASE A — free-path e2e proof (bot-executable now, ~6 min)
STEPS:
1. `cd ~/x402-agent-service && python3 storefront.py stats`
   → baseline JSON (`sales`, `lifetime_usdc`) recorded in the execution note.
2. Create test issue exercising the REJECT path (fake tx must fail on-chain verification):
   `gh issue create -R bettergraininfo-rgb/x402-agent-economy-lab --label x402-order --title "[x402-order] /v1/sentiment (e2e self-test)" --body "tx: 0x1111111111111111111111111111111111111111111111111111111111111111\nendpoint: /v1/sentiment\ntext: storefront e2e reject-path probe"`
3. Run one poll: `python3 storefront.py poll`
4. Verify handling: `gh issue list -R bettergraininfo-rgb/x402-agent-economy-lab --state all --search "e2e self-test"` → issue closed; `gh issue view <N> -R … --comments` shows the
   "Payment could not be verified on-chain" rejection comment.
5. Confirm ledger untouched: `python3 storefront.py stats` → identical to step 1.
   (Fake-tx rejection through the full GitHub path was proven once before; this re-proves it
   on the current code at HEAD.)
6. Commit evidence: append result lines to `org/sales_log.md`; `git add -A && git commit -m "builder: DIR-012 phase-A storefront e2e reject-path proof" && git push`.

VERIFY:
- Step 4 output shows closed issue + rejection comment mentioning the specific reason
  ("tx not found").
- `python3 storefront.py stats` unchanged between steps 1 and 5.
- Exit codes 0 throughout; no ERROR lines in poll stdout.

ROLLBACK:
- Close/delete the test issue: `gh issue close <N> -R bettergraininfo-rgb/x402-agent-economy-lab`.
- Revert the sales_log commit. No server or ledger state is modified in Phase A.

## PHASE B — LIVE paid order (GATED; execute only when condition passes)
GATE CHECK (run first):
```
W=$(python3 -c "import json;print(json.load(open('org/wallet_base_mainnet.json'))['address'])")
curl -s -m 10 https://mainnet.base.org -X POST -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["'$W'","latest"]}'
```
Expected `"result":"0x0"` today → **DO NOT PROCEED**, record `blocked: needs funding` and stop.

If gate passes (ETH ≥ ~0.00005 for gas AND USDC ≥ $0.02):
1. Self-funded live order (net cost ≈ gas only — wallet pays itself):
   build & broadcast a USDC transfer of exactly $0.015 from `$W` to `$W`
   using the repo's EVM signing stack (same pattern as `fund_and_settle.py`); capture tx hash.
2. Open an x402-order issue with that hash, endpoint `/v1/sentiment`.
3. `python3 storefront.py poll` → expect `#N FULFILLED /v1/sentiment $0.015 tx=0x…`.
4. Verify: `python3 storefront.py stats` → sales +1, lifetime_usdc +0.015; issue closed with
   ✅ verified-payment comment; `org/revenue_ledger.json` contains the hash (replay guard armed).
5. Commit evidence to `org/sales_log.md`, push. This satisfies the CEO bar; sales may then
   cite the store in outreach.
ROLLBACK (Phase B): none needed post-fulfillment (self-transfer, funds retained); if the
broadcast fails, no issue is opened and nothing to undo.

ESTIMATED REVENUE IMPACT: $0.015 booked directly (self-test) but this unlocks the entire
demand funnel — after Phase B, every outreach contact can honestly point at a store with a
proven purchase. That gate removal is worth more than any pricing tweak currently queued.

## NOTES
- Phase B spends only dust-level gas from OUR wallet back TO OUR wallet; principal is
  retained. If ETH is absent, do not improvise funding — log blocked and hand to CEO.
- Do not run outreach citing the store until Phase B completes (per DIR-012).
