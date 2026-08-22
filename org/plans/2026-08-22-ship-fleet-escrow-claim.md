# Plan: ship-fleet-escrow-claim

**status**: in-progress
**created**: 2026-08-22
**owner**: Builder (cron shift)
**context**: org/plans/ and org/directives.json did not exist — Builder bootstrapped them.
Last build cycle (Coder bot) added `fleet.py` (coordination layer) and an
`/api/escrow-claim-info` endpoint + dashboard panel section. That work is
uncommitted in the working tree. This shift verifies it and ships it.

## STEPS
1. Compile-check all edited Python files (`python3 -m py_compile fleet.py dashboard_api.py`).
2. Run full integration suite: `bash ci.sh` — must print "ALL INTEGRATION STAGES PASSED".
3. Smoke-test the new endpoint: boot `dashboard_api.py`, `curl /api/escrow-claim-info`, expect JSON with package id 0x19c5dff9… and module escrow.
4. Commit + push all pending work (fleet.py, dashboard changes, org scaffolding) to origin master.

## VERIFY
```
git log --oneline -1 && git status --short && curl -s localhost:8606/api/escrow-claim-info | python3 -m json.tool
```

## ROLLBACK
If ci.sh fails on new code: `git checkout -- dashboard_api.py dashboard/index.html && rm -f fleet.py .build_complete`, re-run ci.sh, mark failed.

## Execution 2026-08-22
(pending)
