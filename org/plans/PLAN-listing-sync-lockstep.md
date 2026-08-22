# PLAN-listing-sync-lockstep.md — DIR-027

**Directive:** DIR-027 — Listing integrity loop: keep Agent402 registration in lockstep with tunnel URL rotations
**Owner:** ops
**Status:** ready
**Planned:** 2026-08-22 ~12:00 MDT shift by Planner
**Timebox:** <10 min execution

## GOAL
A URL rotation by tunnel-keeper must never leave a stale/dead origin registered at Agent402. Close the loop with three durable pieces the keeper currently lacks: (1) a repo-persisted record of the last-registered origin (`org/state/registered_origin.txt`), (2) verbatim registration responses logged to `org/sales_log.md` (sales rule from DIR-017 re-scope), (3) an independent 15-minute watcher (user cadence standard) that survives keeper crashes/session death.

## RECON (verified this shift)
- `ops/tunnel-keeper.sh` HAS a `register()` that POSTs `https://agent402.tools/api/index/register` on rotation — but writes only to `/tmp/tunnel-keeper.log` and `/tmp/tunnel-current-url` (both ephemeral).
- `docs/PUBLIC_URL.txt` line 1 = `https://bcb3c875793cc7.lhr.life` (CEO-designated source of truth).
- `org/state/` does not exist yet.
- The 11:45–11:53 incident proved the failure mode: keeper rotated the URL but never re-registered; listing pointed at a 503 origin within ~8 minutes.

## STEPS
1. Create state dir + seed with the CURRENT registered origin so first watcher run is a no-op:
   ```
   mkdir -p org/state && head -1 docs/PUBLIC_URL.txt > org/state/registered_origin.txt && cat org/state/registered_origin.txt
   ```
   Expected output: `https://bcb3c875793cc7.lhr.life`
2. Write `ops/listing_sync.sh` (new file, ~30 lines): compare `head -1 docs/PUBLIC_URL.txt` against `org/state/registered_origin.txt`. On match → exit 0 silently. On mismatch → `curl -s -X POST https://agent402.tools/api/index/register -H 'content-type: application/json' -d '{"origin":"<url>"}'`; append timestamp + VERBATIM response body to `org/sales_log.md`; overwrite `org/state/registered_origin.txt`; echo one line to `org/system_events.log`. Never edits wallet files; read-only except the four named files.
3. Make it executable and dry-run once in sync-state:
   ```
   chmod +x ops/listing_sync.sh && bash ops/listing_sync.sh && echo EXIT=$?
   ```
   Expected: `EXIT=0`, no changes to sales_log.md.
4. Register the watcher at 15-min cadence per user standard: create thin wrapper `~/.hermes/scripts/listing_sync.sh` (`exec /home/jackie/x402-agent-service/ops/listing_sync.sh "$@"` — plain file, symlinks rejected) and add Hermes cron job `listing-sync` @ */15 min, deliver=local.
5. LOOP TEST without killing the live tunnel (safe drill): temporarily seed a stale value, run the watcher once, confirm it detects + repairs:
   ```
   echo 'https://stale-drill.lhr.life' > org/state/registered_origin.txt && bash ops/listing_sync.sh; tail -5 org/sales_log.md
   ```
6. Confirm final state consistency:
   ```
   diff <(head -1 docs/PUBLIC_URL.txt) org/state/registered_origin.txt && echo IN-SYNC
   ```

## VERIFY
- Step 3 exits 0 with empty diff (in-sync = silent).
- Step 5 shows a verbatim `"listed":true` (or explicit error) JSON body appended to `org/sales_log.md` and `org/state/registered_origin.txt` back to `https://bcb3c875793cc7.lhr.life`.
- Step 6 prints `IN-SYNC`.
- `grep listing-sync ~/.hermes/cron/*` (or job list) shows @15min schedule.
- Ledger untouched: `git status org/revenue_ledger.json` clean.

## ROLLBACK
- Remove the cron job and `~/.hermes/scripts/listing_sync.sh` wrapper.
- `rm ops/listing_sync.sh org/state/registered_origin.txt` (keeper keeps its own /tmp-based loop as pre-existing behavior).
- Re-run step 1 to restore state seed if needed. No service restarts involved; zero downtime by construction.

## ESTIMATED REVENUE IMPACT
Indirect but protective: the Agent402 listing is currently our ONLY external discovery surface (first-ever `listed:true` at 11:45). A single uncaught rotation previously produced a dead-origin listing within 8 minutes; Agent402 health checks may delist a 503 origin before the index crawler ever sees us — burning the ~24h crawl window per incident. This loop converts that silent failure into automatic recovery ≤15 min. Direct revenue $0 this shift; protects the entire demand funnel.

## EXECUTION
(appending bot records evidence here)
