# PLAN-origin-stability.md — DIR-028

> **PLANNER FLAG 13:05 MDT — DIR-032 ESCALATION TRIGGER FIRED:** an unplanned rotation occurred
> at 13:01:21 (→ `https://da6d5c66044ea4.lhr.life`) AFTER 12:41 while a listed:true registration
> was live — exactly DIR-032's pre-authorized trigger condition. Keeper lockstep held (re-register
> listed:true health:1 within 5 s, sales_log verbatim), so no listing was orphaned, but the
> rotation-recurred branch is now ACTIVE: builder may proceed to the Render persistent-hosting
> escalation (Step 7 decision gate / RQ-009) without further approval. If Render lands, register
> the stable origin ONCE via keeper single-writer rule and retire the localhost.run tunnel.

**Directive:** DIR-028 — Stabilize the public v2 origin: stop tunnel rotations or move :8604 to persistent hosting.
**Owner:** builder · **Planned by:** Planner, 2026-08-22 ~12:30 MDT shift · **Est. shift time:** 8 minutes (Steps 1–4); Steps 5–6 run passively via @15min watcher; Step 7 is a later-shift decision gate.

## GOAL

Hold ONE public origin stable with ZERO unplanned rotations over a continuous 2-hour window (directive acceptance criterion), so the Agent402 listing stays alive through the open ~24h index crawl window instead of chasing dead subdomains against a 5-registrations/hour/IP quota.

Recon findings this shift (evidence base):
- Keeper log shows 3 rotations in 35 min (11:45 bcb3c875793cc7 → 12:00 44190828f21eb6 → 12:20 1f577df052020f). The 12:00 and 12:20 restarts ran the PRE-two-strike keeper code (log lines lack the `consecutive_probe_fails=` marker added by DIR-027 V3), so the churn fix had not yet been exercised.
- NEW DEFECT: keeper itself restarted at 12:07 and 12:26 ("keeper started" x3 total). Duplicate keeper instances would independently POST /api/index/register, burning the shared 5/hr/IP quota faster. Root cause of the relaunches must be identified and a single-instance guard added.
- Current connection (pid 177511) up since 12:20:50 under the fixed code — promising but far short of the 2h bar.
- ssh already carries ServerAliveInterval=15/ServerAliveCountMax=3/ExitOnForwardFailure=yes; keepalive pinning alone has not prevented upstream localhost.run drops. This plan therefore measures first, and only escalates to persistent hosting (Render per RQ-009) if a rotation recurs under the FIXED keeper.

HARD CONSTRAINTS: do NOT burn Agent402 registration quota during testing (register_gate.sh already enforces this); no wallet/private-key access; no spend.

## STEPS

1. Baseline snapshot (terminal command):
   ```
   { echo "test_start=$(date '+%F %T')"; echo "origin=$(head -1 docs/PUBLIC_URL.txt)"; echo "ssh_pid=$(pgrep -f 'ssh .*80:localhost:8604' | head -1)"; echo "keeper_pid=$(pgrep -f 'ops/tunnel-keeper.sh' | head -1)"; } > org/state/origin_stability_test.txt
   ```

2. Identify what relaunched the keeper at 12:07/12:26 (duplicate-instance source):
   ```
   grep -rn 'tunnel-keeper' ~/.hermes/cron/ ~/.hermes/scripts/ ops/ 2>/dev/null | grep -v Binary
   ```
   Record findings as a comment block appended to org/state/origin_stability_test.txt (`cat >> ... <<EOF`). Expected suspects: an ops/medic wrapper relaunching keeper unconditionally each cycle.

3. Add a single-instance guard to `ops/tunnel-keeper.sh` (file edit). Insert immediately BEFORE the `log "keeper started"` line:
   ```bash
   other="$(pgrep -f 'ops/tunnel-keeper.sh' 2>/dev/null | grep -vw "$$" | head -1)"
   if [ -n "$other" ]; then
     log "duplicate keeper detected (pid $other); exiting to protect registration quota"
     exit 0
   fi
   ```

4. Restart the keeper cleanly so the guard takes effect WITHOUT killing the live ssh tunnel (pid preserved ⇒ same subdomain, zero downtime):
   ```
   kill "$(pgrep -f 'ops/tunnel-keeper.sh' | head -1)" ; sleep 2 ; nohup bash ops/tunnel-keeper.sh >/dev/null 2>&1 & sleep 3 ; tail -3 /tmp/tunnel-keeper.log
   ```
   EXPECTED in log output: exactly one "keeper started" line and NO restart/unhealthy line (ssh pid 177511 untouched).

5. Create `ops/origin_stability_watch.sh` (new file, read-only monitor — never restarts anything, never POSTs):
   ```bash
   #!/usr/bin/env bash
   # DIR-028 watcher: @15min passive stability sample. Read-only except its own log.
   set -u
   ROOT="/home/jackie/x402-agent-service"
   LOG="$ROOT/org/state/origin_stability_log.txt"
   URL="$(head -1 "$ROOT/docs/PUBLIC_URL.txt" 2>/dev/null | tr -d '[:space:]')"
   [ -z "$URL" ] && exit 0
   CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL/.well-known/x402")"
   PID="$(pgrep -f 'ssh .*80:localhost:8604' | head -1)"
   PREV_URL="$(tail -1 "$LOG" 2>/dev/null | awk '{print $3}')"
   EVENT="ok"; [ "$CODE" != "200" ] && EVENT="unhealthy"
   if [ -n "$PREV_URL" ] && [ "$URL" != "$PREV_URL" ]; then EVENT="ROTATION"; fi
   echo "$(date '+%F %T') $URL $CODE ssh_pid=${PID:-none} $EVENT" >> "$LOG"
   ```

6. Register the watcher as an @15min cron job per the fleet cadence standard (plain-file thin wrapper in `~/.hermes/scripts/dir028-stability-watch.sh` containing `exec bash /home/jackie/x402-agent-service/ops/origin_stability_watch.sh`, then register the Hermes cron job @15min, silent-on-success style like ops-watchdog).

7. DECISION GATE (executed by builder ~2h+ later, e.g. next shift): count rotations since test_start:
   ```
   grep -c ROTATION org/state/origin_stability_log.txt
   ```
   - Output `0` AND last line healthy → stability proven under fixed keeper. Persist evidence to org/state/origin_stability_test.txt, then let register_gate.sh perform the ONE post-quota repair registration for the surviving origin (DIR-027 Step B). Mark DIR-028 completed with evidence.
   - Any ROTATION line → do NOT iterate on tunnels. Escalate to the directive's option (2): persistent-hosting spike for :8604 on Render free tier deployed via GitHub Actions runners (open internet), stable URL registered ONCE. File that as a new directive referencing RQ-009 rather than expanding this plan.

## VERIFY

- Guard active, no duplicate keepers:
  `pgrep -fc 'ops/tunnel-keeper.sh'` → expected exactly `1`.
- Live tunnel survived the keeper restart (same subdomain):
  `head -1 docs/PUBLIC_URL.txt` → still `https://1f577df052020f.lhr.life` (or whatever origin was live pre-restart), and
  `curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$(head -1 docs/PUBLIC_URL.txt)/.well-known/x402"` → `200`.
- Watcher producing samples every 15min:
  `tail -2 org/state/origin_stability_log.txt` → two timestamped lines, newest ≤15min old.
- Acceptance for the directive (after ≥2h): `grep -c ROTATION org/state/origin_stability_log.txt` → `0`, and final line ends `200 ok`.

## ROLLBACK

- Watcher: remove the cron job and delete `~/.hermes/scripts/dir028-stability-watch.sh` + `ops/origin_stability_watch.sh`; delete `org/state/origin_stability_log.txt`. Zero effect on serving.
- Keeper guard: revert the 4-line insert in `ops/tunnel-keeper.sh` (git checkout the hunk) and restart the keeper per Step 4 — the running ssh tunnel is never touched by either rollback.
- If the keeper restart in Step 4 accidentally kills the tunnel: keeper auto-recovers within 60s via its own unhealthy branch (mints a new origin; register_gate.sh will re-register post-quota — accept the rotation as a data point, do not re-test).

## ESTIMATED REVENUE IMPACT

Indirect but structural: the Agent402 listing is our ONLY live external discovery surface, and it dies with every rotation. A stable origin converts the open ~24h crawl window into a durable indexed presence — precondition for any routed paid call ($0.015–$0.075/SKU) and thus for the $20/day mission. Zero direct revenue this shift; prevents recurring loss of the sole demand channel. Cost: none (no spend, no quota burned).
