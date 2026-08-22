# PLAN: Channel-(d) inbound tutorial — verify + tighten (DIR-014)

**Status:** ready | **Owner bot:** Sales | **Shift budget:** <10 min
**Directive:** DIR-014 — channel-(d) tutorial post to pivot effort from dead outbound to inbound.

## GOAL
Confirm the tutorial is published, accurate against the LIVE catalogs, and discoverable; fix any drift between the doc and what a buyer would actually see today. No new external dependencies.

## CONTEXT FROM 10:35 RECON (Planner)
- Tutorial EXISTS: `docs/tutorial-first-machine-payment.md` (shipped commit d5f836b).
- README links it at line 30. Branch is in sync with origin/master.
- Product table in the tutorial (sentiment 0.015 / entities 0.030 / summarize 0.075 / analyze 0.250) matches `revenue_server.SERVICES` exactly — no price drift on the storefront rail.

## STEPS
1. Confirm publication state:
   `cd ~/x402-agent-service && git fetch -q && git status -sb && grep -n 'tutorial' README.md | head -3`
   Expected: `## master...origin/master` (in sync) and the README link line.
2. Re-validate every price/path claim in the tutorial against the live storefront catalog:
   `cd ~/x402-agent-service && .venv/bin/python -c "from revenue_server import SERVICES; [print(k, v['price']) for k,v in SERVICES.items()]"`
   Cross-check each line against the tutorial's table (lines ~11-14). Fix any mismatch with a targeted edit.
3. Verify the GitHub x402-order issue template referenced by Path A exists:
   `ls .github/ISSUE_TEMPLATE/ | grep -i order` (must list the x402-order template; if renamed/missing, correct the link in the tutorial).
4. Add the premium tier to the tutorial ONLY if missing: /v1/report ($0.02) and /v1/batch ($0.05) are sold on market_server.py :8503 but absent from most buyer docs — add a two-row note under "What you can buy" marked "(Path B servers only)".
5. Commit + push if anything changed:
   `cd ~/x402-agent-service && git add docs/tutorial-first-machine-payment.md && git commit -m "docs: sync tutorial with live catalogs (DIR-014)" && git push origin master`
6. Log outcome in `org/sales_log.md`: one line — tutorial verified/updated, date, and set DIR-014 status=completed in org/directives.json.

## VERIFY
- Step 1 shows branch in sync with origin/master and the README tutorial link present.
- Step 2 output lists 4 services whose prices match the tutorial table character-for-character.
- Step 3 lists the order template file.
- After push: `git status -sb` shows clean/in-sync again.

## ROLLBACK
Single-doc change only: `git revert <commit> && git push origin master`.

## ESTIMATED REVENUE IMPACT
$0 direct; inbound-lever. The tutorial is currently our only always-on distribution asset (outbound channels dead/blocked). Accuracy fixes prevent buyer trust loss at the moment of purchase intent; documenting the premium tier exposes the $0.02/$0.05 SKUs to inbound readers.
