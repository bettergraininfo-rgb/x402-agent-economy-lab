# PLAN-premium-endpoint-parity.md (DIR-002)

**Status:** ready | **Owner bot:** Builder | **Shift budget:** <10 min
**Dependency:** run before PLAN-x402-listing-manifest.md (manifest advertises this endpoint).

## GOAL
Ship `/v1/summarize` (our highest-price product) on `sui_market_server.py` so all three services are available on both settlement rails. New price: 0.12 SUI (120,000,000 MIST), matching the premium USD tier.

## STEPS
1. Backup: `cd ~/x402-agent-service && cp sui_market_server.py /tmp/sui_market_server.py.bak`
2. Edit `sui_market_server.py` — replace:
   `"/v1/entity-extract": {"price": 80_000_000, "fn": None},`
   with:
   ```
   "/v1/entity-extract": {"price": 80_000_000, "fn": None},
   "/v1/summarize":      {"price": 120_000_000, "fn": None},
   ```
3. In the same file, insert this function immediately after `svc_entities`:
   ```python
   def svc_summarize(text: str) -> dict:
       import re
       sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
       if len(sents) <= 2:
           return {"summary": text[:280], "sentences_in": len(sents), "sentences_out": len(sents)}
       freq: dict[str, int] = {}
       for w in re.findall(r"[a-z']+", text.lower()):
           if len(w) > 3:
               freq[w] = freq.get(w, 0) + 1
       def score(s):
           ws = re.findall(r"[a-z']+", s.lower())
           return sum(freq.get(w, 0) for w in ws) / max(1, len(ws))
       keep = sorted(range(len(sents)), key=lambda i: -score(sents[i]))[: max(1, len(sents)//3)]
       return {"summary": " ".join(sents[i] for i in sorted(keep)),
               "sentences_in": len(sents), "sentences_out": len(keep)}
   ```
4. Register it next to the others (after the existing `SERVICES["/v1/entity-extract"]["fn"] = svc_entities` line):
   `SERVICES["/v1/summarize"]["fn"] = svc_summarize`
5. Syntax check: `.venv/bin/python -m py_compile sui_market_server.py && echo OK`
6. Restart: `pkill -f 'uvicorn sui_market_server' ; sleep 1 ; cd ~/x402-agent-service && (.venv/bin/uvicorn sui_market_server:app --port 8604 >/tmp/sui_market.log 2>&1 &) ; sleep 3`

## VERIFY
1. `curl -s http://localhost:8604/bazaar | .venv/bin/python -m json.tool` → three entries, including `"endpoint": "/v1/summarize"` with `price_sui: 0.12`.
2. Challenge check: `curl -s "http://localhost:8604/v1/summarize?text=hello"` → HTTP 402 JSON with `"amount_mist": 120000000`.
3. Function smoke test (no payment needed): `.venv/bin/python -c "from sui_market_server import svc_summarize; print(svc_summarize('Sui is fast. Agents need payments. Payments settle on-chain. Fast chains help agents.'))"` → returns a dict with a non-empty `summary`.
Optional full paid-path proof: `.venv/bin/python sui_market_client.py` (uses faucet-funded devnet wallet — no real money).

## ROLLBACK
`cp /tmp/sui_market_server.py.bak sui_market_server.py && pkill -f 'uvicorn sui_market_server'` then restart per step 6. No data migration involved.

## ESTIMATED REVENUE IMPACT
Unlocks the premium SKU on the Sui rail at 1.5–2.4x the price of existing endpoints. If summarize captures ~30% of volume mix at its higher price, blended revenue/call rises ~50%. Zero incremental infrastructure cost.
