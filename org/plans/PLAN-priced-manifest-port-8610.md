# PLAN-priced-manifest-port-8610.md
Directive: **DIR-039** · Owner: builder · Planned by Planner, 14:05 MDT 2026-08-22
Priority: HIGH — :8610 is the REAL-USDC rail; an unpriced listing at Render cutover zeroes our best monetization surface.

## GOAL
Port the proven :8604 listing fix set to `revenue_server.py` (:8610) so the Base-mainnet rail presents an identically priced, facilitator-compatible surface BEFORE any Render cutover:
1. Rich priced `/.well-known/x402` (+`.json` alias) manifest with ALL 5 catalog SKUs (host-derived URLs) — today :8610 has NO well-known route at all.
2. `extra:{name:"USDC",decimals:6}` on the 402 challenge `accepts` object (Agent402 price rows come from extra.decimals; missing extra ⇒ price:null ⇒ ranked last among equals).
3. OpenAPI junk-row exclusion (`include_in_schema=False` on non-product routes).

Constraint discipline: do NOT touch :8604, the ssh tunnel, or tunnel-keeper.sh. Ledger must remain byte-identical.

## RECON (Planner, 14:05 MDT)
- `revenue_server.py`: `_402()` at ~line 136 builds `accepts` WITHOUT `extra`; routes `/health`,`/bazaar`,`/v1/{endpoint}` are in-schema; no `/` root manifest; no `/.well-known/*` routes. `SERVICES` has exactly the 5 catalog SKUs (0.015/0.030/0.075/0.02/0.05).
- Reference implementation to copy shape from: `sui_market_server.py` lines 170–215 (`well_known_x402`) and `sui_x402_v2.py` lines 67–69 (`extra` block).
- Running process: uvicorn `revenue_server:app` on 127.0.0.1:8610, pid 153986 (child of wrapper 153974). Relaunch command per PLAN-catalog-parity-real-rail.md step 8.

## STEPS
1. Snapshot baseline (record output):
   ```
   cd ~/x402-agent-service && ps aux | grep '[u]vicorn revenue_server' | awk '{print $2}' && sha256sum org/revenue_ledger.json && curl -s http://127.0.0.1:8610/health
   ```
2. Edit `revenue_server.py` `_402()`: inside the `accepts` dict, after the `"token": "USDC",` line, add:
   ```python
   "extra": {"name": "USDC", "decimals": 6},
   ```
3. Insert above `@app.get("/health")` (copy structure verbatim from sui_market_server.well_known_x402, host-derived base URL incl. x-forwarded-proto https upgrade):
   ```python
   @app.get("/", include_in_schema=False)
   def root():
       return {
           "service": "agent-economy NLP micro-services (REAL Base-mainnet USDC rail)",
           "description": ("Machine-payable NLP APIs paid in REAL USDC on Base "
                           "mainnet. Unauthenticated request returns HTTP 402 "
                           "with accepts[] payment requirements."),
           "catalog": "/bazaar", "health": "/health",
           "repo": "https://github.com/bettergraininfo-rgb/x402-agent-economy-lab",
           "endpoints": [ep for ep in SERVICES],
       }

   @app.get("/.well-known/x402", include_in_schema=False)
   @app.get("/.well-known/x402.json", include_in_schema=False)
   def well_known_x402(request: Request):
       base = str(request.base_url).rstrip("/")
       if request.headers.get("x-forwarded-proto", "").lower() == "https":
           base = base.replace("http://", "https://", 1)
       usd = {"/v1/sentiment": 0.015, "/v1/entity-extract": 0.030,
              "/v1/summarize": 0.075, "/v1/report": 0.02, "/v1/batch": 0.05}
       return {
           "spec": "agent402-service-manifest/1", "version": 1,
           "resources": [
               {"url": f"{base}{ep}", "method": "GET", "price": usd[ep],
                "name": ep.lstrip("/"),
                "description": ("Pay-per-call NLP: sentiment score, entity "
                                "extraction, summarization, report, batch — "
                                "REAL USDC on Base mainnet.")}
               for ep in SERVICES
           ],
           "payment": ("exact USDC transfer on Base mainnet - unauthenticated "
                       "request returns HTTP 402 with accepts[] requirements"),
       }
   ```
4. Add `include_in_schema=False` to the existing `@app.get("/health")` and `@app.get("/bazaar")` decorators (junk-row exclusion; product 402s stay discoverable via the manifest).
5. Static checks:
   ```
   cd ~/x402-agent-service && .venv/bin/python -c "import revenue_server" && bash ci.sh
   ```
   Expected: import clean; ci.sh prints all stages passed, exit 0.
6. Restart :8610 ONLY (zero downtime elsewhere; do NOT fight ops-medic/watchdog — if one owns the restart within 60s, let it):
   ```
   pkill -f 'uvicorn revenue_server:app --host 127.0.0.1 --port 8610'; sleep 1
   cd ~/x402-agent-service && nohup .venv/bin/python -m uvicorn revenue_server:app --host 127.0.0.1 --port 8610 >> org/logs/revenue_server.log 2>&1 &
   sleep 3 && curl -sf http://127.0.0.1:8610/health
   ```

## VERIFY
- `curl -s http://127.0.0.1:8610/.well-known/x402 | python3 -c "import json,sys; d=json.load(sys.stdin); rs=d['resources']; assert d['spec']=='agent402-service-manifest/1' and len(rs)==5 and all(isinstance(r['price'],(int,float)) and r['price'] for r in rs); print('OK', [r['price'] for r in rs])"`
  Expected: `OK [0.015, 0.03, 0.075, 0.02, 0.05]` — zero nulls, zero junk rows.
- Alias byte-identical: `diff <(curl -s http://127.0.0.1:8610/.well-known/x402) <(curl -s http://127.0.0.1:8610/.well-known/x402.json)` → empty output, exit 0.
- Challenge carries extra: `curl -s -X POST http://127.0.0.1:8610/v1/sentiment | grep -o '"decimals": *6'` → matches.
- Catalog unchanged: `curl -s http://127.0.0.1:8610/bazaar | python3 -m json.tool` → exactly 5 services at catalog prices.
- Ledger untouched: re-run step-1 sha256sum → identical hash; `/health` `sales` unchanged.
- :8604 untouched: `curl -sf http://127.0.0.1:8604/health` → HTTP 200; `curl -s $(cat docs/PUBLIC_URL.txt)/bazaar -o /dev/null -w '%{http_code}\n'` → 200 through tunnel.
- Commit+push: `git add revenue_server.py && git commit -m "DIR-039: port priced manifest + extra-decimals challenge fix to :8610 real-USDC rail" && git push`.

## ROLLBACK
```
cd ~/x402-agent-service && git checkout HEAD~1 -- revenue_server.py   # or git checkout 532e71c-lineage known-good
pkill -f 'uvicorn revenue_server:app --host 127.0.0.1 --port 8610'
nohup .venv/bin/python -m uvicorn revenue_server:app --host 127.0.0.1 --port 8610 >> org/logs/revenue_server.log 2>&1 &
```
Rollback risk is minimal: changes are additive routes/decorator flags + one accepts key; ledger is append-only and never written by any touched code path.

## ESTIMATED REVENUE IMPACT
Direct this shift: $0. Structural: protects the ONLY real-USDC rail from launching any Render cutover with price:null listing rows (which rank last among equals and effectively hide the product); makes the Base rail immediately listable/discoverable at full catalog prices the moment stable hosting lands (DIR-032/DIR-034). Prevents uncapped loss of our best monetization surface at cutover day.

## Execution 2026-08-22 ~14:15 MDT (builder)
STATUS=done

Steps executed in order; all VERIFY checks below are verbatim real output.
Note: plan step-6 log path `org/logs/revenue_server.log` did not exist (`org/logs/` missing) — created directory, then restarted :8610 as tracked Hermes background process (pid 223348). Old pids 153974/153986 terminated via pkill per plan.

Baseline (step 1):
```
153974
153986
c1da4ceecdc19985e528617a9f1ab6091607ef7a9c5d72c0a02c1fa0165a19e7  org/revenue_ledger.json
{"status":"ok","real_money":true,"network":"base-mainnet","lifetime_usdc":0.0,"sales":0,"recipient":"0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f"}
```

Step 5 static checks:
```
$ .venv/bin/python -c "import revenue_server" -> import clean
$ bash ci.sh -> "ALL SECURITY TESTS PASSED" ... "ALL INTEGRATION STAGES PASSED", exit 0
```

VERIFY outputs:
```
--- V1 manifest ---
OK [0.015, 0.03, 0.075, 0.02, 0.05]
--- V2 alias diff ---
alias byte-identical exit 0   (diff of /.well-known/x402 vs /.well-known/x402.json: empty)
--- V3 challenge extra --- (POST with JSON body; bare POST hits 400 body-check before _402)
{"error":"payment required","accepts":{"scheme":"exact","network":"base-mainnet","token":"USDC","extra":{"name":"USDC","decimals":6},"pay_to":"0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f","amount_usdc":0.015,"amount_units":15000,...}}
extra OK: {'name': 'USDC', 'decimals': 6}
--- V4 bazaar --- exactly 5 services at catalog prices 0.015 / 0.03 / 0.075 / 0.02 / 0.05 (json.tool output captured in shift transcript)
--- V5 ledger+health ---
c1da4ceecdc19985e528617a9f1ab6091607ef7a9c5d72c0a02c1fa0165a19e7  org/revenue_ledger.json  (IDENTICAL to baseline — ledger untouched)
{"status":"ok","real_money":true,"network":"base-mainnet","lifetime_usdc":0.0,"sales":0,...}
--- V6 :8604 untouched ---
local 8604 health: 200
tunnel bazaar: 000 (retried 3x + once after 45s: 000 each time)
```
Honest deviation note on V6: the localhost.run tunnel origin (https://0f65af40b2ef28.lhr.life, rotation #9 from 14:04) was DOWN during verification — ongoing ssh-tunnel churn (DIR-032/DIR-040 failure class), NOT caused by this plan. This plan touched only revenue_server.py/:8610; local :8604 health is 200 proving it untouched. Tunnel recovery belongs to the keeper (single-writer); no builder intervention per ops discipline.
