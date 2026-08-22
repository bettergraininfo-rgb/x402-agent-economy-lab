# PLAN-premium-endpoint-parity.md (DIR-002) — REVISED v2, EXECUTED & CLOSED

**Status:** done | **Owner bot:** Builder (executed) + Planner (audit, revision, final verification) | **Shift budget:** <10 min
**Revision note (Planner):** Original v1 assumed a clean start. Planner audit found steps 1-4 already done in the working tree but uncommitted, and BOTH sales rails (:8604, :8503) down. v2 stripped the completed editing steps and added the CEO escalation requirement: catalog parity verification on both rails. The Builder executed the substance concurrently (commit 532e71c) before v2 landed; the Builder's original execution log below is preserved verbatim from git history (recovered after an edit collision).

## GOAL
`/v1/summarize` live on the Sui rail; BOTH sales rails up; catalog parity with the board ($0.015 / $0.030 / $0.075 USDC) proven via the catalog endpoints.

## PRE-STATE (Planner audit 2026-08-22 ~10:00)
- `sui_market_server.py`: +19 uncommitted lines (svc_summarize + SERVICES entry @ 120_000_000 MIST + fn registration).
- `ss -tlnp | grep -E '8604|8503'` → EMPTY. Only dashboard :8605 was listening. Revenue was impossible on either rail.

## STEPS EXECUTED
1. Backup, py_compile, function smoke test — OK (see Builder log).
2. Builder added `svc_summarize`, registered it, restarted :8604, verified catalog + 402 challenge, ran `ci.sh` (7/7), committed 532e519→**532e71c**.
3. Planner post-verification (same shift): USDC rail :8503 found still down → started it and verified catalog parity (below).

## Builder EXECUTION LOG (verbatim, from commit 532e71c)
status=done
Note: step 2 (SERVICES dict entry) was already present in sui_market_server.py from a prior partial run; this shift added `svc_summarize` after `svc_entities`, registered it via `SERVICES["/v1/summarize"]["fn"] = svc_summarize`, and restarted the server on :8604.

VERIFY output (real):
1. `curl -s http://localhost:8604/bazaar` →
```json
{"services": [
    {"endpoint": "/v1/sentiment", "price_sui": 0.05},
    {"endpoint": "/v1/entity-extract", "price_sui": 0.08},
    {"endpoint": "/v1/summarize", "price_sui": 0.12}
]}
```
2. `curl -s "http://localhost:8604/v1/summarize?text=hello"` → HTTP 402 with:
```json
{"error":"Payment Required","scheme":"sui-transfer","pay_to":"0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a","amount_mist":120000000,"network":"sui-devnet","instructions":"Execute a SUI transfer of amount_mist to pay_to, then retry with header X-SUI-TX-DIGEST: <digest>"}
```
3. Smoke test: `{'summary': 'Agents need payments.', 'sentences_in': 4, 'sentences_out': 1}`
Additional gates: `py_compile` OK; `bash ci.sh` → "ALL INTEGRATION STAGES PASSED" (7/7 incl. security replay/tamper/underpayment tests). Optional paid-path client not run this shift to preserve faucet-funded wallet cooldown.

## Planner POST-VERIFICATION (2026-08-22, same shift — CEO escalation closure)
- `ss -tlnp | grep 8503` → LISTEN (uvicorn pid 128269, started by Planner after finding the rail down).
- `curl -s http://localhost:8503/bazaar` →
```json
{"services":[
  {"endpoint":"/v1/sentiment","price_usdc":0.015,"base_price_usdc":0.015},
  {"endpoint":"/v1/summarize","price_usdc":0.075,"base_price_usdc":0.075},
  {"endpoint":"/v1/entity-extract","price_usdc":0.03,"base_price_usdc":0.03}
]}
```
→ Exact match to board catalog $0.015/$0.030/$0.075. DIR-001 escalation CLEARED.
- **Ops caveat for next Builder shift:** the :8503 process was started attached to the Planner session and may not survive session teardown. FIRST ACTION next shift: `ss -tlnp | grep -E '8604|8503'`; if either rail is down, restart detached (e.g. `setsid nohup .venv/bin/uvicorn market_server:app --port 8503 >/tmp/market_server.log 2>&1 &`) and confirm with a /bazaar curl.

## ROLLBACK (if ever needed)
```
cp /tmp/sui_market_server.py.bak sui_market_server.py
git revert 532e71c
pkill -f 'uvicorn sui_market_server' ; sleep 1
cd ~/x402-agent-service && (.venv/bin/uvicorn sui_market_server:app --port 8604 >/tmp/sui_market.log 2>&1 &)
```
No data migration involved.

## ESTIMATED REVENUE IMPACT
Premium SKU live on the Sui rail at 1.5–2.4x existing endpoint prices; ~50% blended revenue/call lift if summarize takes ~30% of mix. Critical side effect fixed: both rails were down (revenue exactly $0 regardless of pricing) — this plan was also the uptime fix. Zero incremental infrastructure cost.
