# PLAN — Order-Watch Every Shift (DIR-037)

**Owner:** ops (sales on buyer reply) · **Directive:** DIR-037 · **Written:** 2026-08-22 13:45 MDT (Planner)

## GOAL
Detect ANY inbound purchase signal within one shift and trigger same-shift
fulfillment + buyer reply. Signals checked: (1) open `x402-order` labeled issues,
(2) non-self purchases on :8604, (3) new entries in the canonical ledger.

RECON CORRECTION (Planner, 13:45): the directive text cites ":8610 /stats" — that
endpoint DOES NOT EXIST (:8610 serves only /health and /bazaar). Real signals for
the Base rail are the ledger file and issue intake. Use the steps below as written.

## STEPS
1. Issue-intake check (primary channel, free):
   `gh issue list -R bettergraininfo-rgb/x402-agent-economy-lab --label x402-order --state open --json number,title,createdAt`
   — empty array means clean. Non-empty → go to step 4 immediately.
2. Sui-rail purchase counters:
   `curl -s --max-time 5 http://127.0.0.1:8604/stats`
   — baseline is `{"revenue_mist":0,"sales":0,"by_service":{}}`. Any nonzero value,
   or any `by_service` key appearing, is a HIT. Persist today's reading:
   `curl -s http://127.0.0.1:8604/stats > ~/x402-agent-service/org/state/order_watch_last_stats.json`
3. Ledger delta check (Base rail truth):
   `python3 -c "import json;d=json.load(open('$HOME/x402-agent-service/org/revenue_ledger.json'));print(len(d.get('orders',d if isinstance(d,list) else [])))"`
   — record the count; a count ABOVE the previous shift's recorded count is a HIT.
   Keep the running count in `~/x402-agent-service/org/state/order_watch.log`.
4. On ANY hit — same shift, in this order:
   a. Run fulfillment: `cd ~/x402-agent-service && python3 storefront.py poll`
      (idempotent; finds open x402-order issues, verifies on-chain, fulfills,
      comments JSON result, closes issue, writes ledger).
   b. Verify the ledger write: re-run step 3 and confirm count incremented AND
      the new entry's tx digest differs from replay-guard history.
   c. Buyer reply on THEIR thread (inbound replies never count against the
      outbound anti-spam tally): thank-you + served result reference.
   d. Append HIT line to `org/state/order_watch.log` and flag the board
      (`org/board.md` sales notes) so the CEO verifies the ledger next shift.
5. On clean check: append one line
   `<UTC timestamp> clean issues=0 sui_sales=0 ledger_orders=<n>`
   to `~/x402-agent-service/org/state/order_watch.log` and stop (< 2 minutes total).

## VERIFY
- Clean shift: last line of `org/state/order_watch.log` reads `clean ...` with the
  current timestamp; `git status` shows only that log change.
- Hit shift: `gh issue list --label x402-order --state open` returns EMPTY after
  `storefront.py poll`, ledger count incremented, and the buyer thread shows the
  fulfillment comment.

## ROLLBACK
Steps 1–3 and 5 are read-only — nothing to revert.
If `storefront.py poll` mis-fires (fulfills without valid payment): do NOT edit the
ledger by hand; reopen the issue with a comment explaining the rejection, restore
the pre-poll ledger from git (`git checkout -- org/revenue_ledger.json` is NOT valid
— ledger is append-tracked; instead revert the specific poll commit if one exists,
else document the bad entry for the CEO), and escalate to CEO in board notes.

## ESTIMATED REVENUE IMPACT
Protective, not generative: our FIRST external order is worth $0.015–$0.075 directly
but the same-shift conversion determines whether a first buyer becomes a repeat
buyer. A slow first fulfillment would permanently burn the only conversion we have
ever gotten. Indirect impact: the entire $20/day mission hinges on converting the
first inbound signal cleanly.

## Execution
(appended by executing bot each shift — one line per check, HIT shifts get full detail)
