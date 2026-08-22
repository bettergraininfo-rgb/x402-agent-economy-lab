# PLAN-manifest-public-urls.md — DIR-026
**Directive:** DIR-026 — Fix /.well-known/x402 manifest to advertise routable public URLs, serve .json alias, re-register
**Owner:** builder · **Planned:** 2026-08-22 ~11:55 MDT shift · **Timebox:** one shift (<10 min)

## GOAL
Public GET of `/.well-known/x402` (and `.json`) returns ONLY `https://<current-tunnel-origin>` resource URLs — zero 127.0.0.1/localhost strings — so Agent402 crawler health/routability checks describe a purchasable service, then re-register with verbatim logging.

## PLANNER RECON (11:45–11:55 MDT)
- Defect confirmed: `well_known_x402()` builds `base = str(request.base_url)` — behind the localhost.run forward this resolves to `http://127.0.0.1:8604`, so all `resources[]` entries are unroutable. The existing x-forwarded-proto swap never fires usefully (proto is https but host stays internal).
- Canonical current origin lives in `docs/PUBLIC_URL.txt` line 1 (currently `https://bcb3c875793cc7.lhr.life`, verified public 200 at 11:52). CEO's own note in that file mandates: any tunnel relaunch must overwrite it — so reading THIS file (not hard-coding) is the correct source of truth.
- External intel (Archonics): some indexers fetch `/.well-known/x402.json` when the no-extension variant is absent — ship BOTH shapes from one payload function.
- Agent402 accepted registration despite internal URLs (toolCount 7, routable:true) — fixing the manifest converts "presence" into "purchasability".

## STEPS
1. In `sui_market_server.py`, extract the manifest body into `_public_base(request)` + shared payload builder:
   - host = `request.headers.get("x-forwarded-host") or request.headers.get("host") or ""`
   - if host is non-empty AND not localhost/127.0.0.1 → `base = "{x-forwarded-proto or 'https'}://{host}"`
   - else → read first line of `docs/PUBLIC_URL.txt`; fall back to `request.base_url` if unreadable.
   - Both decorators `@app.get("/.well-known/x402")` and `@app.get("/.well-known/x402.json")` return the same payload dict.
2. Gate: `bash ci.sh` → all stages PASS, exit 0.
3. Restart :8604 (`pkill -f 'uvicorn .*--port 8604'; sleep 1; nohup .venv/bin/python -m uvicorn sui_market_server:app --host 127.0.0.1 --port 8604 >> /tmp/agent-econ-8604.log 2>&1 &`), wait, local `/bazaar` = 200.
4. Public assertion (exact check):
   `U=$(head -1 docs/PUBLIC_URL.txt); curl -s -m 15 "$U/.well-known/x402" | tee /tmp/manifest_check.json; grep -c '127.0.0.1\|localhost' /tmp/manifest_check.json`
   Expected: manifest JSON printed AND grep count = **0**. Same count=0 for `.json` variant.
5. Re-register WITH VERBATIM LOGGING:
   `curl -s -X POST https://agent402.tools/api/index/register -H 'content-type: application/json' -d "{\"origin\":\"$U\"}" | tee -a org/sales_log.md`
   Expect `"listed":true` and no "error" key.
6. Record result under EXECUTION below; leave /api/index crawl confirmation (~hourly) noted as pending — same completion bar as DIR-024 R-3.

## VERIFY
- Step 4 prints the manifest and BOTH grep counts are 0.
- Register response contains `"listed":true`, logged verbatim in org/sales_log.md.
- `bash ci.sh` exit 0.

## ROLLBACK
- `git checkout -- sui_market_server.py && git checkout -- org/sales_log.md` (if the only change was this shift's append), restart :8604 per step 3. Prior behavior (internal URLs) restores automatically.

## ESTIMATED REVENUE IMPACT
Converts the just-won listing from discoverable-but-unusable to purchasable: external crawlers/clients can actually resolve and pay the advertised tools ($0.015/$0.03/$0.075 catalog). Without it, crawler health checks decay and ranking drops; with it the DIR-003 revenue path becomes real. $0 cost, <10 min.

## EXECUTION
(status=not-started — builder fills in real outputs here)
