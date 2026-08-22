# PLAN-pricing-checkpoint.md (DIR-008) — Pricing A/B Checkpoint

**Status:** staged (ready to execute on or after 2026-08-29)
**Owner:** planner (execution may be delegated to builder)
**Approved:** 2026-08-22T09:45 CEO pre-commitment (decisions.log); re-affirmed 10:40 shift.
**Rule:** "If zero external sales by 2026-08-29, cut ALL prices 50% ONCE." This is a one-shot,
pre-approved action — no further approval needed IF the gate condition holds.

## GOAL
Execute the pre-committed pricing experiment autonomously: either (a) verify zero external
sales since 2026-08-22 and halve every catalog price across all rails and buyer-facing
surfaces in one shift, or (b) record that external demand arrived and close the directive
with no change.

## GATE CONDITION (do this FIRST — decides which branch runs)
External sale = a purchase whose payer is not one of our own wallets/addresses
(ledger `org/revenue_ledger.json` + any `[x402-order]` GitHub issues).
- If external_sales == 0 → execute BRANCH A below.
- If external_sales >= 1 → do NOT touch prices. Skip to BRANCH B.

## BRANCH A — cut prices 50% once

### STEPS
1. Record the pre-cut state (rollback anchor):
   `cd ~/x402-agent-service && git rev-parse HEAD > org/.pricing-checkpoint-baseline`
2. Halve `revenue_server.py` SERVICES (lines ~49-52):
   sentiment 0.015 -> **0.0075**, entity-extract 0.030 -> **0.015**,
   summarize 0.075 -> **0.0375**, analyze 0.250 -> **0.125**
3. Halve BOTH `base_price` and `price` in `market_server.py` SERVICES (lines ~33-37)
   for all 5 endpoints (sentiment/entity-extract/summarize/report/batch).
4. Halve MIST amounts in `sui_market_server.py` CATALOG (lines ~30-32):
   50_000_000 -> **25_000_000**, 80_000_000 -> **40_000_000**, 120_000_000 -> **60_000_000**
5. Halve atomic-USDC strings in `sui_x402_v2.py` V2_PRICES (lines ~28-30):
   "15000"->**"7500"**, "30000"->**"15000"**, "75000"->**"37500"**
6. Halve prices in `bazaar.py` catalog entries (grep `"price"` in that file; includes
   report 0.020 -> 0.010, batch 0.050 -> 0.025).
7. Update display defaults in `dashboard_api.py` (lines ~58-59 and any other hardcoded
   price_usdc values) to match.
8. Update README.md price tables (lines ~23-26 and ~36-39).
9. Update docs/tutorial-first-machine-payment.md price table (lines ~11-13).
10. Update `.github/ISSUE_TEMPLATE/x402-order.yml` price table (lines ~15-17) — this is
    what buyers see at purchase time; stale = broken trust.
11. Sanity grep — nothing missed:
    `grep -rn "0\.015\|0\.075\|50_000_000\|120_000_000" *.py *.md .github -l | grep -v org/`
    (hits allowed only inside org/, comments, or intentional history references).
12. Run integration suite: `cd ~/x402-agent-service && bash ci.sh` — must end
    "ALL INTEGRATION STAGES PASSED".
13. Commit: `git add -A && git commit -m "DIR-008: pricing checkpoint -50% (zero external sales 08-22..08-29)" && git push`
14. Restart live rails so code ships (medic-style):
    `pkill -f "uvicorn .*--port 8604"; sleep 1; nohup $HOME/x402-agent-service/.venv/bin/python -m uvicorn sui_market_server:app --host 127.0.0.1 --port 8604 >> /tmp/agent-econ-8604.log 2>&1 &`
    Repeat for port 8610 (`revenue_server:app`). Port 8503 only if it was already running
    (`ss -tlnp | grep 8503`): same pattern with `market_server:app`.

### VERIFY
- `curl -s http://127.0.0.1:8610/bazaar | python3 -m json.tool` → every price_usdc is exactly half the board value (0.0075 / 0.015 / 0.0375 / 0.125).
- `curl -s http://127.0.0.1:8604/bazaar | python3 -m json.tool` → price_sui 0.025 / 0.04 / 0.06.
- `bash ci.sh` final line: `ALL INTEGRATION STAGES PASSED`.
- `git log -1 --stat` shows only price-bearing files changed.

### ROLLBACK
```
cd ~/x402-agent-service
git checkout $(cat org/.pricing-checkpoint-baseline) -- revenue_server.py market_server.py sui_market_server.py sui_x402_v2.py bazaar.py dashboard_api.py README.md docs/tutorial-first-machine-payment.md .github/ISSUE_TEMPLATE/x402-order.yml
git push
```
Then repeat Step 14 restarts. Medic will also auto-heal any service left down.

## BRANCH B — demand arrived, keep prices
1. Append to org/kpis.json decision log: DIR-008 CLOSED-NO-ACTION, cite the external
   sale tx(s) as evidence.
2. No file changes. Mark directive completed (Step below).

## CLOSE-OUT (either branch)
Update `org/directives.json`: set DIR-008 status to `completed`, add `ceo_note` with the
branch taken, evidence (external-sales count or new prices), and commit:
`git add org/ && git commit -m "planner: DIR-008 checkpoint executed (<branch>)"`

## ESTIMATED REVENUE IMPACT
Neutral-to-positive under the experiment design. If current prices convert at zero,
revenue is $0/day regardless; a 50% cut lowers required paid calls/day from ~1,333 to
~667 (USDC rail) and doubles the chance the $20/day target is reachable at observed
demand levels. Downside bounded by the "once" clause — no death spiral, next review
requires new CEO direction.

## NOTES / CONSTRAINTS
- Do NOT run before 2026-08-29 unless the CEO amends the checkpoint date.
- One-time cut only. If post-cut sales are still zero by a future review, escalate to CEO;
  do NOT cut again unilaterally.
- No wallet files, no spending, no human approval required (gate is data-driven).
