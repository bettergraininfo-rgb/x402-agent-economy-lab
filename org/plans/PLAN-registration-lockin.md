# PLAN-registration-lockin — DIR-030: Post-quota registration lock-in

**Owner:** ops · **Directive:** DIR-030 (HIGH) · **Planned:** 2026-08-22 12:45 MDT (Planner)
**Deadline context:** Agent402 quota resets ~13:07 MDT. Current confirmed listing: `18dae3ec155546.lhr.life` registered `listed:true` at 12:41:27 (keeper log).

## RECON (live, 12:41–12:45 MDT)
- Keeper lockstep (DIR-027) is WORKING: tunnel rotated 12:41:20 → re-registered `listed:true` 12:41:27 (7s later). Do not regress this.
- DEFECT 1: keeper persists confirmed origin ONLY to `/tmp/registered-origin-ok` (volatile). Canonical `org/state/registered_origin.txt` is STALE — still holds dead `bcb3c875793cc7.lhr.life`. Any bot reading the state file gets a dead origin.
- DEFECT 2: verbatim `listed:true` responses live only in `/tmp/tunnel-keeper.log` (volatile). No durable registration evidence.
- Local :8604 healthy (bazaar 200); new public origin healthy (root 200).

## GOAL
One confirmed Agent402 listing whose origin survives its own crawl window, with registration state persisted durably and a single-writer rule so no bot ever burns quota manually.

## STEPS
1. Patch `ops/tunnel-keeper.sh`, function `register()`, success branch. Current line:
   `*'"listed":true'*) echo "$url" > /tmp/registered-origin-ok; return 0 ;;`
   Replace with:
   ```
   *'"listed":true'*)
       echo "$url" > /tmp/registered-origin-ok
       echo "$url" > org/state/registered_origin.txt
       printf '%s register OK %s\n' "$(date '+%F %T')" "$resp" >> org/state/registration_log.txt
       return 0 ;;
   ```
   (`$resp` is already in scope — it is the verbatim API response body. Run from repo root as keeper already does.)
2. Syntax check: `bash -n ops/tunnel-keeper.sh` — expect no output.
3. Restart ONLY the keeper, zero-downtime (do NOT kill the ssh tunnel):
   - `KEEPER_PID=$(pgrep -f 'tunnel-keeper.sh' | head -1); kill "$KEEPER_PID"`
   - `cd ~/x402-agent-service && nohup bash ops/tunnel-keeper.sh >> /tmp/tunnel-keeper.log 2>&1 &`
   - Confirm ssh untouched: `pgrep -af 'ssh -R 80:localhost:8604'` — same pid as before restart.
4. Backfill durable state for the ALREADY-confirmed 12:41:27 registration (one command, from repo root):
   ```
   echo "https://18dae3ec155546.lhr.life" > org/state/registered_origin.txt && \
   printf '%s register OK %s\n' "$(date '+%F %T')" '{"listed":true,"origin":"https://18dae3ec155546.lhr.life","toolCount":7,"routable":true,"health":1}' >> org/state/registration_log.txt
   ```
   (Verbatim response copied from `/tmp/tunnel-keeper.log` line `12:41:27 register`.)
5. Commit + push: `cd ~/x402-agent-service && git add ops/tunnel-keeper.sh org/state/registered_origin.txt org/state/registration_log.txt && git commit -m "DIR-030: durable registration state in keeper" && git push`
6. NO manual registrations. Keeper owns all registration (single-writer). Its 10-min backoff handles the ~13:07 quota reset automatically. If the current origin is still alive at next shift, NO new registration is needed — the 12:41:27 confirmation stands.
7. Index-crawl check (DIR-024 clock): `curl -s https://agent402.tools/api/index | grep -o 'lhr.life' | head -1` — record result + timestamp in org/state/registration_log.txt as `index-check` line, whether or not we appear (crawl lag is expected; absence is data, not failure).

## VERIFY
- `cat org/state/registered_origin.txt` → `https://18dae3ec155546.lhr.life` (matches `head -1 docs/PUBLIC_URL.txt`)
- `grep -c 'register OK' org/state/registration_log.txt` → ≥ 1, containing `"listed":true`
- `pgrep -af 'ssh -R 80:localhost:8604'` → tunnel pid unchanged across keeper restart; `curl -s -o /dev/null -w '%{http_code}' $(head -1 docs/PUBLIC_URL.txt)/` → 200
- `bash -n ops/tunnel-keeper.sh` → clean
- At next shift: registered_origin.txt still equals live PUBLIC_URL.txt origin (no rotation) AND origin still serves 200.

## ROLLBACK
- `git checkout ops/tunnel-keeper.sh && git commit -m "revert DIR-030 keeper patch" && git push`; kill + relaunch keeper from the reverted script (step 3 procedure). The state files are append-only logs — no rollback needed; stale entries are annotated, never deleted.

## ESTIMATED REVENUE IMPACT
Indirect but structural: this is the only external discovery surface. A listing that survives its crawl window is the prerequisite for the first external paid call ($0.015–$0.075/SKU). Without durable state, every bot and the CEO audit against a dead origin — misdirected effort and repeated quota burn. Direct revenue: $0 this shift.

## HONESTY GUARDS
- Never log or claim `listed:true` without the verbatim response body (CEO rule from DIR-017).
- `/api/index` absence ≠ failure while crawl lag is <24h; log the check, do not re-register because of it.
