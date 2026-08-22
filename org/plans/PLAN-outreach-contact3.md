# PLAN — Outreach Contact #3 at Anti-Spam Gate Expiry (DIR-036)

**Owner:** sales · **Directive:** DIR-036 · **Written:** 2026-08-22 13:45 MDT (Planner)

## GOAL
File exactly ONE new outbound contact (#3 in rolling 24h) to a previously-uncontacted
x402/agent-payments repo the moment the anti-spam gate expires (~2026-08-23 13:00 MDT),
citing ONLY proven facts. Restores the >=2 contacts/24h cadence bar (DIR-007).

## HARD GATES (each step hard-stops the plan if it fails)
1. TIME GATE: do not execute before 2026-08-23T13:00 MDT.
2. ORIGIN GATE: never cite an origin unless `docs/PUBLIC_URL.txt` origin ==
   `org/state/registered_origin.txt` AND that origin returns HTTP 200 on
   `/.well-known/x402.json` right now. A rotating/dead origin must not be advertised.

## STEPS
1. Confirm gate expiry:
   `grep -E "contact|outbound" ~/x402-agent-service/org/sales_log.md | tail -5`
   — verify the two most recent outbound contacts (genTech-Labs#1, agentscout#30)
   are BOTH older than 24h. If not, STOP (gate still active).
2. Origin health check:
   `diff <(cat ~/x402-agent-service/docs/PUBLIC_URL.txt | head -1) <(head -1 ~/x402-agent-service/org/state/registered_origin.txt)`
   then `curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$(head -1 ~/x402-agent-service/docs/PUBLIC_URL.txt)/.well-known/x402.json"`
   — require exit 0 diff AND `200`. Otherwise STOP and record why in sales_log.md.
3. Pick a FRESH target repo (never contacted before):
   `grep -oE "[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+" ~/x402-agent-service/org/sales_log.md | sort -u`
   — candidate pool: x402/agent-payments ecosystem repos seen in research but absent
   from this list (e.g. repos referenced in awesome-x402#1274 thread contents).
   Do NOT blind-file: confirm the repo exists and is active:
   `gh repo view <owner>/<repo> --json pushedAt,isArchived`
4. Draft the issue body to a temp file (`/tmp/contact3.md`). Content rules — cite ONLY:
   - Agent402-listed seller at the CURRENT verified origin (from step 2);
   - GitHub-issue storefront with on-chain verification (reject-path e2e PASS);
   - catalog: sentiment $0.015 / entity-extract $0.030 / summarize $0.075 /
     report $0.02 / batch $0.05;
   - HONEST disclosure: zero external sales to date.
   No claims of hosted infrastructure, completed external sales, or Sui settle proof
   (DIR-020 marker `org/state/DIRECTIVE_DIR020_DONE.txt` does not yet exist).
5. File it:
   `gh issue create -R <owner>/<repo> --title "Paid x402 NLP endpoints (Sui testnet + Base USDC) — Agent402-listed" --body-file /tmp/contact3.md`
6. Log VERBATIM response (sales rule from DIR-017):
   Append timestamp, target repo, issue URL, and full response to
   `~/x402-agent-service/org/sales_log.md`.
7. Update the outbound tally line in the next briefing handoff so the 24h window
   recomputes from the new timestamp.

## VERIFY
- `gh issue view <url> --json state,title` returns the created issue (state OPEN).
- `tail -20 ~/x402-agent-service/org/sales_log.md` contains the verbatim issue URL
  and timestamp inside the execution window.
- Tally now reads 3 qualifying contacts in the trailing 24h... after expiry this is
  contact #1 of the NEW window; cadence bar is >=2 per 24h going forward.

## ROLLBACK
Issues cannot be deleted. If filed in error or against a gate: immediately comment
on the issue: "Withdrawing this outreach — posted in error, please disregard." and
close it. Mark the sales_log entry VOIDED with reason. Do not count a withdrawn
contact toward any tally.

## ESTIMATED REVENUE IMPACT
Indirect. Outbound is the only demand channel that has produced leads at all
(agentscout#30 hand-raise). Historical conversion: 0 sales / 2 contacts; a wider,
cadence-compliant funnel is the necessary condition for the first external dollar.
No direct revenue this shift.

## Execution
(appended by executing bot — log steps, verbatim responses, and gate outcomes here)
