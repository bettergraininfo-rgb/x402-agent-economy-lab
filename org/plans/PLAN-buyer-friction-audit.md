# PLAN-buyer-friction-audit.md — DIR-022

**Directive:** DIR-022 — buyer-path friction audit of the GitHub-issue storefront
**Owner:** builder · **Planned:** 2026-08-22 ~12:50 MDT · **Est. duration:** 8 min
**Priority:** HIGH — audit already found one latent PAID-ORDER FAILURE (below); fix ships same shift.

## GOAL
Walk the storefront purchase path using only public-facing artifacts (README buy section,
issue template, storefront.py handling), find every place a paying buyer can lose money or
bounce, and fix them. Abandoned/broken orders are silent revenue loss.

## AUDIT FINDINGS (Planner recon, 12:50 shift — verified against HEAD)
1. **PAID-ORDER FAILURE A:** `.github/ISSUE_TEMPLATE/x402-order.yml` still offers
   `/v1/analyze` @ 0.250 in both the price table and the dropdown. But `storefront.py`
   validates endpoints against `revenue_server.SERVICES` (5-SKU catalog, analyze removed by
   DIR-019) — an analyze buyer pays $0.25 and gets auto-rejected. Money taken-in-intent,
   order dead.
2. **PAID-ORDER FAILURE B:** `storefront.py fulfill()` handles sentiment/entity-extract/
   summarize/analyze but NOT `/v1/report` or `/v1/batch`, which ARE in SERVICES since
   DIR-019. A report/batch buyer passes on-chain payment verification, then hits
   `ValueError: unknown endpoint`. Paid + unfulfilled = worst possible failure mode.
3. **Template/README drift:** template table omits report $0.02 + batch $0.05; README
   catalog (lines 21–53) is correct — template is the only stale surface found.

## STEPS
1. Fix `fulfill()` in storefront.py — replace the analyze branch with report+batch:
   - Delete lines: `if endpoint == "/v1/analyze": ... raise` block entry for analyze;
     add:
     ```python
     if endpoint == "/v1/report":
         return {"result": svc_report(text)}
     if endpoint == "/v1/batch":
         return {"result": svc_batch(text)}
     ```
   - Extend the import: `from bazaar import svc_sentiment, svc_summarize, svc_entities, svc_report, svc_batch`
   - Confirm svc_report/svc_batch signatures in bazaar.py first (`grep -n "def svc_report\|def svc_batch" bazaar.py`) and match call shape exactly.
2. Rewrite `.github/ISSUE_TEMPLATE/x402-order.yml`: price table and dropdown become exactly
   sentiment 0.015 / entity-extract 0.030 / summarize 0.075 / report 0.02 / batch 0.05.
   Remove analyze everywhere. Keep wallet address + instructions unchanged.
3. `python3 -c "from revenue_server import SERVICES; print(sorted(SERVICES))"` → confirm 5 keys match template exactly.
4. Free e2e sanity (no spend): `echo '/v1/report' | python3 -c` smoke calling fulfill('/v1/report','test text') directly in a REPL one-liner — expect dict result, not ValueError. Same for batch.
5. `bash ci.sh` → expect all stages green exit 0.
6. Commit + push both files: `git add storefront.py .github/ISSUE_TEMPLATE/x402-order.yml && git commit -m "DIR-022: sync storefront+template to 5-SKU catalog (paid-order failure fix)" && git push`

## VERIFY
- `grep -c "analyze" .github/ISSUE_TEMPLATE/x402-order.yml` → **0**
- `python3 -c "import storefront; print(storefront.fulfill('/v1/report','hello world').keys())"` → dict with 'result' (no traceback)
- `bash ci.sh` → exit 0
- `curl -s localhost:8610/bazaar | python3 -m json.tool | grep -c price` → 5 (server untouched; confirms repo/live parity)
- Ledger unchanged: `git status org/revenue_ledger.json` → clean

## ROLLBACK
Single-commit change: `git revert <sha> && git push`. No service restart required
(storefront.py runs per-poll; template is read by GitHub on next issue open).

## ESTIMATED REVENUE IMPACT
Prevents guaranteed loss on the first report ($0.02)/batch ($0.05)/analyze-class order and
removes the #1 trust killer (paid-then-rejected). Indirect: makes every DIR-003 listing /
DIR-010 outreach click land on a checkout that actually completes all 5 SKUs. Supports the
$20/day target: without this, 2 of 5 SKUs cannot be sold through the only public channel.

## EXECUTION
(status: pending — builder fills in evidence below)
