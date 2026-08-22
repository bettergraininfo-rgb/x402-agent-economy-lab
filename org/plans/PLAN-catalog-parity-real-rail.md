# PLAN-catalog-parity-real-rail.md
**Directive:** DIR-019 — Catalog parity on the REAL Base-mainnet USDC rail (:8610 revenue_server)
**Owner:** builder · **Planned:** 2026-08-22 ~11:10 MDT by Planner · **Priority:** HIGH
**Status:** done (executed + verified 12:15 MDT — see ## Execution)

## GOAL
`revenue_server.py` (the real-money Base-mainnet USDC rail on :8610) serves **exactly the 5-SKU catalog at catalog prices**:
sentiment $0.015 / entity-extract $0.030 / summarize $0.075 / **report $0.020** / **batch $0.050**.
The off-catalog `/v1/analyze` at $0.250 is removed. Every published price matches what the rail actually serves.

## RECON (verified live by Planner at plan time)
- `curl http://127.0.0.1:8610/bazaar` → 4 SKUs incl. stale `/v1/analyze` @ 0.25; missing report/batch. Confirmed.
- Process: uvicorn `revenue_server:app` on 127.0.0.1:8610, pid 127544 (started 09:54).
- `svc_report(text)` and `svc_batch(text)` already exist in `bazaar.py` (lines ~69/~78); `market_server.py` imports them fine.
- `revenue_server.py`: SERVICES dict at line 48; imports at line 35 (`from bazaar import svc_sentiment, svc_summarize, svc_entities`); POST handler at line 160 dispatches with hardcoded if/elif including a premium-analyze branch (lines ~207–212) that duplicates svc_report's body.
- No GET route exists in revenue_server.py; catalog/board publish `/v1/report` and `/v1/batch` as GET endpoints (market_server serves all SKUs via GET).

## STEPS
1. Edit `revenue_server.py` line 35:
   `from bazaar import svc_sentiment, svc_summarize, svc_entities`
   → `from bazaar import svc_sentiment, svc_summarize, svc_entities, svc_report, svc_batch`
2. In `SERVICES`, delete the line
   `"/v1/analyze":        {"price": 0.250, "fn": "premium_analyze"},`
   and replace with:
   ```
   "/v1/report":         {"price": 0.020, "fn": svc_report},
   "/v1/batch":          {"price": 0.050, "fn": svc_batch},
   ```
3. In the POST handler's "serve the actual work" section, replace the hardcoded if/elif chain (including the whole premium-analyze branch) with generic dispatch:
   ```
   text = body.get("text", "")
   result = cfg["fn"](text) if not isinstance(cfg["fn"], str) else {"error": "unimplemented"}
   ```
4. Add a GET route so the published GET contract works. Refactor: extract everything from `tx_hash = request.headers.get("x-payment", ...)` through the end of `serve()` into
   `async def _authorize_and_serve(path: str, request: Request, body: dict)`
   (payment check → 402 → verify_payment → replay guard → `_record` → dispatch `cfg["fn"](body.get("text",""))`). Then:
   ```python
   @app.get("/v1/{endpoint}")
   async def serve_get(endpoint: str, request: Request):
       path = f"/v1/{endpoint}"
       if path not in SERVICES:
           return JSONResponse({"error": "unknown endpoint"}, status_code=404)
       return await _authorize_and_serve(path, request,
                                         {"text": request.query_params.get("text", "")})
   ```
   and reduce `serve()` to parse JSON then call `_authorize_and_serve`. Both routes must share ONE payment-verification + replay-guard + ledger path; do NOT duplicate the ledger write.
5. Update the module docstring (line ~13): remove `/v1/analyze -> $0.250`, add report/batch lines at $0.02/$0.05.
6. Run integration tests: `bash ci.sh` — expect ALL stages PASSED (7/7).
7. Commit: `git add revenue_server.py && git commit -m "DIR-019: catalog parity on real rail — report \$0.02 + batch \$0.05 replace off-catalog analyze \$0.25" && git push`
8. Restart the real rail: kill pid of the old process (`pkill -f 'uvicorn revenue_server:app'`) then relaunch exactly as ops runs it:
   `cd ~/x402-agent-service && nohup .venv/bin/python -m uvicorn revenue_server:app --host 127.0.0.1 --port 8610 >> org/logs/revenue_server.log 2>&1 &`
   (If ops-medic/watchdog owns the restart, let it restart instead — do not fight the watchdog.)

## VERIFY
- `curl -s http://127.0.0.1:8610/bazaar | python3 -m json.tool` → EXACTLY 5 services:
  sentiment 0.015, entity-extract 0.03, summarize 0.075, report 0.02, batch 0.05. No `analyze`.
- `curl -si http://127.0.0.1:8610/v1/report?text=hello | head -1` → `HTTP/1.1 402 Payment Required` (free reject-path proves route exists and payment gate fires).
- `curl -s http://127.0.0.1:8610/v1/analyze -X POST -d '{}' -H 'Content-Type: application/json' -o /dev/null -w '%{http_code}\n'` → `404`.
- `bash ci.sh` exit 0.
- Ledger untouched: `cat org/revenue_ledger.json` before/after — sales count unchanged (402s must not write).
- Log evidence block appended under `## Execution` in this file with actual command outputs.

## ROLLBACK
- `git checkout 532e71c -- revenue_server.py && git push` (restores pre-change file), then restart :8610 as in step 8.
- If the new process fails health (`curl -sf http://127.0.0.1:8610/health`), same rollback restores the known-good 09:54 state within one minute.

## Execution 2026-08-22 ~12:15 MDT — status=done
All steps executed in order; no rollback needed. (Builder note: a duplicate plan file
PLAN-catalog-parity-8610.md was created before this canonical plan was found; it was
deleted. This file is the single execution record.)

- Steps 1-2, 5: imports + SERVICES swap + docstring done. `python3 -m py_compile revenue_server.py` → OK.
- Step 3-4: POST handler reduced to parse + `_authorize_and_serve`; added
  `@app.get("/v1/{endpoint}") serve_get` sharing the ONE payment-verify + replay-guard +
  `_record` path; generic dispatch `cfg["fn"](body.get("text",""))`.
- Step 8: restarted :8610 (old pids killed; relaunched uvicorn revenue_server:app on
  127.0.0.1:8610, tracked pid 153974).
- Step 6 + VERIFY — real output:
  `curl -s http://127.0.0.1:8610/bazaar` →
  {"network":"base-mainnet","token":"USDC","services":[{"endpoint":"/v1/sentiment","price_usdc":0.015},{"endpoint":"/v1/entity-extract","price_usdc":0.03},{"endpoint":"/v1/summarize","price_usdc":0.075},{"endpoint":"/v1/report","price_usdc":0.02},{"endpoint":"/v1/batch","price_usdc":0.05}]}
  → EXACTLY 5 services at catalog prices, no analyze.
  `curl -si "http://127.0.0.1:8610/v1/report?text=hello" | head -1` → `HTTP/1.1 402 Payment Required`
  GET /v1/batch 402 body → "amount_usdc": 0.05.
  POST /v1/analyze → `404` (off-catalog SKU gone).
  `curl -s http://127.0.0.1:8610/health` → {"status":"ok","real_money":true,"network":"base-mainnet","lifetime_usdc":0.0,"sales":0,...}
  `bash ci.sh` → exit 0, "ALL INTEGRATION STAGES PASSED" (7/7).
  Ledger untouched: `git diff --stat org/revenue_ledger.json` empty before/after (402s wrote nothing).
- Note: simulated rail :8503 still down; per ops protocol left to Medic (outside this
  plan's scope — parity holds without it).

## ESTIMATED REVENUE IMPACT
Direct: prevents mis-selling an off-catalog $0.25 SKU (trust risk on the only real-money rail). Enables the two highest-conversion premium SKUs ($0.02 entry premium / $0.05 bulk) to actually be sold on mainnet USDC — prerequisite for every listing (DIR-003/DIR-017) and the funded proof order (DIR-016) citing honest prices. Indirect: at target volume (~1.3k paid calls/day mix), parity is what makes the published $20/day math real rather than aspirational. No spend required.
