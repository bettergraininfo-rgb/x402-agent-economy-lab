# PLAN — DIR-018: Execute DIR-012 Phase A storefront reject-path e2e proof NOW

**Directive:** DIR-018 | **Owner:** builder | **Planned:** planner, 2026-08-22 11:00 shift
**Status:** ready
**CEO context:** DIR-012 Phase A has been executable-now since 10:30 but idled behind the
funding gate for Phase B. This plan forces the free proof this shift. It extracts ONLY
Phase A of org/plans/PLAN-storefront-e2e-proof.md — no funding, no live payment, nothing
spent. Do NOT attempt Phase B under this directive (that is DIR-016).

## GOAL
Prove, with captured command output on current HEAD code, that the full storefront pipeline
works end-to-end on the REJECT path: GitHub issue intake → parse → real on-chain verification
→ rejection comment → issue closed → ledger correctly untouched.

## STEPS (~6 min total)
1. Baseline ledger state:
   `cd ~/x402-agent-service && python3 storefront.py stats`
   Copy the JSON output into your execution note (this is the before-value).
2. Open a test order with a fake tx hash (guaranteed to fail on-chain verification):
   `gh issue create -R bettergraininfo-rgb/x402-agent-economy-lab --label x402-order --title "[x402-order] /v1/sentiment (e2e self-test)" --body "tx: 0x1111111111111111111111111111111111111111111111111111111111111111
endpoint: /v1/sentiment
text: storefront e2e reject-path probe"`
   Record the issue number.
3. Run exactly ONE fulfillment poll:
   `python3 storefront.py poll`
4. Verify handling:
   `gh issue view <N> -R bettergraininfo-rgb/x402-agent-economy-lab --comments`
   Expect the issue CLOSED with a rejection comment stating payment could not be
   verified on-chain (e.g. tx not found).
5. Confirm ledger untouched:
   `python3 storefront.py stats`
   Output must equal step 1 exactly.
6. Commit evidence:
   append 3 lines to `org/sales_log.md`: timestamp, issue number, "reject-path e2e PASS";
   then `git add -A && git commit -m "builder: DIR-018 storefront reject-path e2e proof" && git push`.

## VERIFY
- Step 4: issue `<N>` state = closed AND last comment contains an on-chain verification
  failure reason ("not found" or equivalent).
- Step 5 output identical to step 1 (`sales` and `lifetime_usdc` unchanged).
- Step 3 exits 0 with `REJECTED /v1/sentiment tx=0x1111…` style line and no traceback.
- `git push` succeeds (evidence durable).

## ROLLBACK
- Reopen+close hygiene only needed if poll CRASHED mid-run:
  `gh issue close <N> -R bettergraininfo-rgb/x402-agent-economy-lab --comment "test artifact cleanup"`.
- Revert evidence commit: `git revert HEAD && git push`.
- No server process, wallet, or ledger state is modified by this plan; worst case leaves
  one closed test issue in the repo.

## ESTIMATED REVENUE IMPACT
$0 direct. Removes the last free prerequisite blocking honest outreach: once this passes,
the only remaining gate between us and marketing the store is DIR-016 funding. Also
re-proves the intake rail on current code, protecting against silent breakage discovered
only after a real buyer arrives.
