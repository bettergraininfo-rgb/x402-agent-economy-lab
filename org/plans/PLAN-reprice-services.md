# PLAN-reprice-services.md (DIR-001)

**Status:** ready | **Owner bot:** Builder | **Shift budget:** <10 min

## GOAL
Raise service base prices ~15x on the USDC rail so the call volume needed for the $20/day target drops from ~20,000/day to ~1,300/day. New price list:

| Endpoint | Old base | New base |
|---|---|---|
| /v1/sentiment | $0.001 | $0.015 |
| /v1/entity-extract | $0.002 | $0.030 |
| /v1/summarize | $0.005 | $0.075 |

Dynamic pricing stays bounded [0.4x, 3x] around the new bases — no logic changes.

## STEPS
1. Backup: `cd ~/x402-agent-service && cp market_server.py /tmp/market_server.py.bak && cp dashboard_api.py /tmp/dashboard_api.py.bak`
2. Edit `market_server.py` — replace the SERVICES block:
   - old: `"/v1/sentiment":      {"base_price": 0.001, "price": 0.001, "fn": svc_sentiment},`
   - new: `"/v1/sentiment":      {"base_price": 0.015, "price": 0.015, "fn": svc_sentiment},`
   - old: `"/v1/summarize":      {"base_price": 0.005, "price": 0.005, "fn": svc_summarize},`
   - new: `"/v1/summarize":      {"base_price": 0.075, "price": 0.075, "fn": svc_summarize},`
   - old: `"/v1/entity-extract": {"base_price": 0.002, "price": 0.002, "fn": svc_entities},`
   - new: `"/v1/entity-extract": {"base_price": 0.030, "price": 0.030, "fn": svc_entities},`
3. Syntax check: `.venv/bin/python -m py_compile market_server.py && echo OK`
4. Edit `dashboard_api.py` — update the three hardcoded `price_usdc` values (lines ~55-57): `0.001`→`0.015`, `0.002`→`0.030`, `0.005`→`0.075`.
5. Syntax check: `.venv/bin/python -m py_compile dashboard_api.py && echo OK`
6. Restart the live market server if running: `pkill -f 'uvicorn market_server' ; sleep 1 ; cd ~/x402-agent-service && (.venv/bin/uvicorn market_server:app --port 8503 >/tmp/market_server.log 2>&1 &) ; sleep 3`
7. Update `org/board.md` product table prices to 0.015 / 0.030 / 0.075.
8. Commit: `cd ~/x402-agent-service && git add market_server.py dashboard_api.py org/board.md && git commit -m "DIR-001: reprice services ~15x (breakeven volume 20k->1.3k calls/day)"`

## VERIFY
`curl -s http://localhost:8503/bazaar | .venv/bin/python -m json.tool`
Expected: sentiment 0.015, entity-extract 0.03, summarize 0.075 (± dynamic drift within [0.4x, 3x] of new bases).
Also: `git log --oneline -1` shows the DIR-001 commit.

## ROLLBACK
`cp /tmp/market_server.py.bak market_server.py && cp /tmp/dashboard_api.py.bak dashboard_api.py && git checkout -- market_server.py dashboard_api.py org/board.md` then restart the server (step 6 command).

## ESTIMATED REVENUE IMPACT
Revenue per sale rises ~15x. Breakeven volume for $20/day falls from ~20,000 to ~1,300 calls/day. Risk: conversion drop from higher prices; monitor `/stats` after 48h — if daily sales fall >15x vs baseline, revert to old bases (rollback above).
