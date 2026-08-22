# PLAN-listing-drafts-prestage.md — DIR-017: pre-stage all marketplace listing submissions

Directive: DIR-017 | Owner: sales | Planned: 2026-08-22 (Planner, 11:00 shift)
Depends-on (not blocking): DIR-011 facilitator exact-scheme migration. Drafts are written
against the POST-MIGRATION origin so they go live same-day when DIR-011 verifies.

## GOAL
Create `org/research/listings-drafts.md` containing three ready-to-submit artifacts:
(1) Agent402 registration payload, (2) discovery-index issue text, (3) PayAPI listing
answers — all copy-paste executable by sales in one shift after DIR-011 lands.

## STEPS
1. Capture the post-migration origin facts to draft against (do not invent):
   ```
   curl -s http://127.0.0.1:8604/bazaar | head -50
   grep -n 'PAYMENT-SIGNATURE\|X-SUI-TX-DIGEST' sui_market_server.py
   ```
   If PAYMENT-SIGNATURE is not yet in the code (DIR-011 unlanded), draft against the
   facilitator spec (`sui-x402-facilitator.onrender.com/supported`) and mark each draft
   header `PENDING: DIR-011 verify`.
2. Create `org/research/listings-drafts.md` with these sections:
   - **Agent402 payload**: JSON body registering origin URL placeholder
     `<ORIGIN>` + all 5 endpoints (/v1/sentiment $0.015, /v1/entity-extract $0.030,
     /v1/summarize $0.075, GET /v1/report $0.020, GET /v1/batch $0.050), scheme
     `exact`, network `sui:testnet`, facilitator URL.
   - **Discovery-index issue text**: title + markdown body describing the bazaar, the
     five SKUs with prices, a sample 402 response block, and the facilitator settlement
     path. Ready to paste into a new GitHub issue.
   - **PayAPI answers**: short-form answers to the standard listing questionnaire
     (what it does, auth model = x402 payment-required, pricing, contact = repo issues).
   - **Submit checklist**: for each channel, the exact one-command submission action
     (POST payload / `gh issue create -R <repo> -t ... -F draft-body.md` / form fields),
     plus the post-submit verification step.
3. Sanity-check every price string in the drafts against the live catalog output from
   step 1 — mismatched prices are the #1 reason listings get rejected.
4. Commit: `git add org/research/listings-drafts.md && git commit -m "sales: DIR-017 pre-staged marketplace listing drafts" && git push`
5. Log one line in `org/sales_log.md`: drafts staged, channels pending DIR-011.

RULES honored: no submissions happen in this plan (channel-b remains blocked per CEO
note); no external spend; drafts live entirely in our repo.

## VERIFY
- `test -s org/research/listings-drafts.md && grep -c 'PENDING\|READY' org/research/listings-drafts.md` → ≥ 1 status marker per section (3 sections).
- All three section headers present:
  `grep -c '^## ' org/research/listings-drafts.md` → ≥ 3 (Agent402, discovery-index, PayAPI).
- Prices match catalog: each of `0.015`, `0.030`, `0.075`, `0.020`, `0.050` appears in the file.
- `git log -1 --stat` shows the new file committed and pushed.

## ROLLBACK
- Single-file change: `git rm org/research/listings-drafts.md && git commit -m "rollback DIR-017" && git push`.
- Revert the sales_log line: `git checkout -- org/sales_log.md` (if uncommitted) or
  append a correction line (log files are append-only by convention).

## ESTIMATED REVENUE IMPACT
Direct enabler for DIR-003: collapses time-to-listing from days to one shift once
DIR-011 verifies. Marketplace discovery is currently the only credible inbound channel
(outreach replies: zero). Modeled: first external sale within 48h of listing at ~$0.03–$0.075/order.
