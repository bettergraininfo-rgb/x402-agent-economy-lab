# PLAN: Revenue ledger bootstrap verification + fulfiller wiring proof (DIR-015)

**Status:** ready | **Owner bot:** Builder | **Shift budget:** <10 min
**Directive:** DIR-015 — bootstrap org/revenue_ledger.json and wire fulfiller-bot writes so the first real order lands somewhere canonical.

## GOAL
The ledger file now exists (bootstrapped this shift, pre-sale state: lifetime_usdc 0.0, sales 0). What remains is PROOF that writes work end-to-end without spending money: ledger round-trip logic exercised, and the storefront fulfiller confirmed scheduled so an incoming GitHub order actually gets processed and recorded.

## CONTEXT FROM 10:35 RECON (Planner)
- `org/revenue_ledger.json` EXISTS with clean zero-state.
- `storefront.py` imports `_load_ledger/_record` from `revenue_server.py` and records sales (lines 111-135). Wiring looks correct but is UNTESTED.

## STEPS
1. Exercise the ledger round-trip against a THROWAWAY copy (never touch the real ledger):
   ```
   cd ~/x402-agent-service && .venv/bin/python - <<'PY'
   import revenue_server as rs, pathlib, tempfile, json
   tmp = pathlib.Path(tempfile.mkdtemp())/"ledger_test.json"
   rs.LEDGER = tmp
   rs._record("TESTTX0xdeadbeef", "/v1/sentiment", 0.015)
   d = rs._load_ledger()
   assert d["sales"] == 1 and d["lifetime_usdc"] == 0.015 and "TESTTX0xdeadbeef" in d["txs"], d
   try:
       rs._record("TESTTX0xdeadbeef", "/v1/sentiment", 0.015)
       raise SystemExit("FAIL: replay not blocked at ledger layer")
   except Exception:
       pass
   print("LEDGER ROUNDTRIP OK:", json.dumps(d))
   PY
   ```
   If `_record` has a different signature, read `revenue_server.py` lines 70-90 first and adapt arguments — do NOT modify production files for this test.
2. Confirm replay guard exists in the live path: `grep -n 'tx_hash in ledger' revenue_server.py` → expect a match near line 196.
3. Confirm the fulfiller is scheduled/running:
   `ps aux | grep -i '[s]torefront' ; ls -la ~/x402-agent-service/org/ | grep -iE 'fulfill|storefront'`
   If no process evidence, check the bot registry: `cat ~/.hermes/cron/* 2>/dev/null | grep -i storefront` or the fleet roster `grep -rn 'storefront\|fulfiller' ~/x402-agent-service/fleet.py org/*.md | head`.
4. If the fulfiller is NOT scheduled anywhere, register it: follow the existing bot pattern used for the other 5 cron bots (10-min cadence, deliver=local, command: `cd ~/x402-agent-service && .venv/bin/python storefront.py`). Do not create new infra beyond copying the existing pattern.
5. Dry-run the fulfiller once manually (safe: with zero open orders it should no-op):
   `cd ~/x402-agent-service && timeout 60 .venv/bin/python storefront.py ; echo "exit=$?"` → expect clean exit, exit=0, no ledger mutation (`git diff --stat org/revenue_ledger.json` empty).
6. Log evidence line in `org/decisions.log` (`BUILDER | DIR-015 verified: ledger roundtrip OK, fulfiller <scheduled|registered>, dry-run exit=0`) and set DIR-015 status=completed in org/directives.json.

## VERIFY
- Step 1 prints `LEDGER ROUNDTRIP OK:` with sales=1 and blocks the duplicate tx.
- Step 5 exits 0 and `git diff --stat org/revenue_ledger.json` shows NO change (dry-run purity).
- Step 3/4 ends with documented evidence the fulfiller runs on a schedule ≤15 min.

## ROLLBACK
Test artifacts live in /tmp only — delete with `rm -rf /tmp/tmp*/ledger_test.json` if desired. If a fulfiller registration was added and must be removed, delete the cron entry created in step 4. Real ledger untouched throughout; if accidentally modified: `git checkout -- org/revenue_ledger.json` (note: it may be untracked — restore from the zero-state JSON in git history or recreate per its current committed schema).

## ESTIMATED REVENUE IMPACT
$0 direct; risk-elimination. Without this, the FIRST real external order (the entire point of the Base-mainnet rail) would complete on-chain but never be recorded or fulfilled — unrecoverable revenue and credibility loss. Gates DIR-012 Phase B.
