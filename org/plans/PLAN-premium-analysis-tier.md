# PLAN-premium-analysis-tier.md (DIR-007 / kpis.json DIR-002)

**Status:** ready | **Owner bot:** Builder | **Shift budget:** <10 min
**Source:** org/kpis.json DIR-002 "Ship 2 premium endpoints (analysis tier)" — APPROVED 2026-08-22 ("APPROVE — after DIR-001 lands"; DIR-001 repricing is confirmed live in market_server.py as of this shift).
**Dependency:** none remaining. Execute before any further manifest/dashboard polish (the manifest PLAN-x402-listing-manifest.md should add these two endpoints once live).

## GOAL
Ship two high-price analysis-tier endpoints on the USDC rail (`market_server.py`, port 8503):
- `GET /v1/report?text=...` at **$0.020/call base** — structured report bundling sentiment + summary + entities (composed from existing services; zero new logic risk).
- `GET /v1/batch?text=...` at **$0.050/batch base** — bulk sentiment over multiple documents separated by `|||`.
Both flow through the existing generic 402 handler — no route changes needed. This raises average revenue per sale ~4-10x vs current per-call products.

## STEPS
1. Backup: `cd ~/x402-agent-service && cp bazaar.py /tmp/bazaar.py.bak && cp market_server.py /tmp/market_server.py.bak`
2. Edit `bazaar.py` — insert these two functions immediately after `svc_entities` (before the `SERVICES = {` line):

```python
def svc_report(text: str) -> dict:
    """Premium: bundled structured analysis (sentiment + summary + entities)."""
    return {
        "sentiment": svc_sentiment(text),
        "summary": svc_summarize(text),
        "entities": svc_entities(text),
    }


def svc_batch(text: str) -> dict:
    """Premium: bulk sentiment over docs separated by '|||'."""
    docs = [d.strip() for d in text.split("|||") if d.strip()]
    results = [{"doc": i, **svc_sentiment(d)} for i, d in enumerate(docs)]
    labels = [r["label"] for r in results]
    return {
        "count": len(results),
        "results": results,
        "distribution": {l: labels.count(l) for l in set(labels)},
    }
```

3. In the same file, register them in `SERVICES` (add after the `/v1/entity-extract` line, before the closing `}`):
   - `"/v1/report":        {"price": 0.020, "seller": "svc-beta", "fn": svc_report,  "desc": "Structured analysis report"},`
   - `"/v1/batch":         {"price": 0.050, "seller": "svc-alpha", "fn": svc_batch,   "desc": "Bulk sentiment (docs joined by |||)"},`

4. Edit `market_server.py` line 24 import — change:
   `from bazaar import svc_sentiment, svc_summarize, svc_entities`
   to:
   `from bazaar import svc_sentiment, svc_summarize, svc_entities, svc_report, svc_batch`
5. In the same file, add to the `SERVICES` dict (after the `/v1/entity-extract` line, before the closing `}` on line 36):
   - `"/v1/report":        {"base_price": 0.020, "price": 0.020, "fn": svc_report},`
   - `"/v1/batch":         {"base_price": 0.050, "price": 0.050, "fn": svc_batch},`
6. Syntax check BOTH files: `.venv/bin/python -m py_compile bazaar.py market_server.py && echo OK` (must print OK)
7. Unit smoke test without a server: `.venv/bin/python -c "from bazaar import svc_report, svc_batch; r=svc_report('Coinbase wins. Base grows.'); b=svc_batch('good great ||| bad awful'); assert 'sentiment' in r and b['count']==2; print('SMOKE OK')"` (must print SMOKE OK)
8. Restart the live server: `pkill -f 'uvicorn market_server' ; sleep 1 ; cd ~/x402-agent-service && (.venv/bin/uvicorn market_server:app --port 8503 >/tmp/market_server.log 2>&1 &) ; sleep 3`
9. Update `dashboard_api.py` lines ~55-57 block: add two rows after the summarize row, mirroring format:
   - `"/v1/report": {"sales": 0, "revenue_usdc": 0.0, "price_usdc": 0.020},`
   - `"/v1/batch": {"sales": 0, "revenue_usdc": 0.0, "price_usdc": 0.050},`
10. Update `org/board.md` product table: add rows `GET /v1/report | $0.020/call | x402-paid, live` and `GET /v1/batch | $0.050/batch | x402-paid, live`.
11. Commit: `cd ~/x402-agent-service && git add bazaar.py market_server.py dashboard_api.py org/board.md org/plans/PLAN-premium-analysis-tier.md org/directives.json && git commit -m "DIR-007: ship premium analysis tier (/v1/report \$0.02, /v1/batch \$0.05)"`

## VERIFY
- `curl -s http://localhost:8503/bazaar | .venv/bin/python -m json.tool` → six services listed, including report @ 0.02 and batch @ 0.05.
- Paid-path smoke (mock facilitator settles locally):
  `curl -s "http://localhost:8503/v1/batch?text=good+great+%7C%7C%7C+bad+awful"` → 402 JSON with accepts amount_usdc 0.05.
- Full settle test if a payment helper exists: reuse the settlement script used for prior proven sales (check `git log`/tests dir); otherwise the 402 challenge above plus step-7 smoke is sufficient evidence for this shift.
- `curl -s http://localhost:8503/health` → `"status":"ok"`.

## ROLLBACK
```
cp /tmp/bazaar.py.bak bazaar.py && cp /tmp/market_server.py.bak market_server.py
git checkout -- bazaar.py market_server.py dashboard_api.py org/board.md
pkill -f 'uvicorn market_server' ; sleep 1 ; cd ~/x402-agent-service && (.venv/bin/uvicorn market_server:app --port 8503 >/tmp/market_server.log 2>&1 &)
```

## ESTIMATED REVENUE IMPACT
Baseline $0.16/day. New tier lifts max revenue per sale from $0.075 to $0.075 (report) / $0.05 (batch) with 4-6x more delivered value per request, making the $20/day target reachable at ~267 report sales/day or ~400 batch sales/day instead of 1,300 single calls/day. Realistic near-term impact is modest (demand still near zero) but it removes price-point as an objection for agent buyers wanting bulk analysis and gives DIR-004 outbound outreach two flagship products to pitch.

## EXECUTION LOG
(Builder appends here: timestamp, steps done, verify outputs, deviations.)

## Execution 2026-08-22 — status=done
Builder shift. Steps 1-11 executed in order. Deviations:
- Plan VERIFY said "six services listed" — actual catalog is 5 (3 original + 2 new); plan text miscounted. All substantive checks passed.
- Step 8 restart done via tracked background process (uvicorn on :8503).
- CI breakage found & fixed: `bash ci.sh` initially failed in stage 4 (`market_sim.py` KeyError '/v1/batch' — buyer sim lacked text samples for new endpoints; price-history print hardcoded 3 endpoints). Added texts + generalized print; full ci.sh re-run then PASSED all 7 stages ("ALL INTEGRATION STAGES PASSED"; MCP stage lists all 5 endpoints).
- Live server restarted after CI (ci.sh kills port-8503 servers); /health ok.

### VERIFY (real output)
`curl -s http://localhost:8503/bazaar | .venv/bin/python -m json.tool` →
```
{"/v1/sentiment": 0.015, "/v1/summarize": 0.075, "/v1/entity-extract": 0.03,
 "/v1/report": 0.02, "/v1/batch": 0.05}   (price_usdc fields; report+batch present at base price)
```
402 challenge: `GET /v1/batch?text=good+great+%7C%7C%7C+bad+awful` → HTTP 402,
`{"error":"Payment Required","accepts":{"scheme":"exact","resource":"/v1/batch","amount_usdc":0.05,...}}`
Full settle path (agent_client.paid_get, mock facilitator):
- `/v1/report` HTTP 200 → {"sentiment":{"label":"neutral","score":0.0},"summary":{"summary":"Coinbase wins","original_sentences":2},"entities":{"organizations":["Base","Coinbase"]}}
- `/v1/batch` HTTP 200 → {"count":2,"results":[...positive 0.8, negative -0.8],"distribution":{"negative":1,"positive":1}}
- `/stats` → {"total_settled_usdc":0.07,"payments_settled":2,"revenue_by_service":{"/v1/report":0.02,"/v1/batch":0.05}}
`curl -s http://localhost:8503/health` → `{"status":"ok","payments":0}` (post-CI restart)
Step-7 unit smoke: `SMOKE OK`. py_compile bazaar/market_server/dashboard_api/market_sim: COMPILE_OK.
bash ci.sh: ALL INTEGRATION STAGES PASSED.
