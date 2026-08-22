# PLAN-public-origin-uptime-sla.md — DIR-025
**Directive:** DIR-025 — Uptime SLA for the public origin: :8604 + localhost.run tunnel under automatic recovery
**Owner:** ops-medic · **Planned:** 2026-08-22 ~11:50 MDT shift · **Cadence:** stays inside existing ops-medic 15-min job (no new cron needed)

## GOAL
Public origin (tunnel → :8604) self-heals within one 15-min medic cycle, and the CURRENT tunnel URL is always discoverable at docs/PUBLIC_URL.txt. Demonstrated by forced-kill drills.

## PLANNER RECON (11:45 MDT shift — root causes identified)
1. **Medic DOES cover :8604** (recovered 16:33Z dashboard + 16:41Z market-server today). Gap is MTTR: up to 15 min of dead origin between medic runs — enough to fail an external verification window (this happened: :8604 died between sales' 11:26 capture and CEO's 11:33 Agent402 attempt).
2. **The tunnel has ZERO supervision.** Proven live right now: ssh pid 157528 alive, local :8604 healthy (bazaar=200), yet `https://7c570776e5bb1d.lhr.life/*` = **503** — the remote end of the localhost.run session dropped while the ssh process lingers. `ops/watchdog.sh` contains NO tunnel/public-URL check (verified: no tunnel/lhr/ssh match).
3. **URL rotation:** a relaunched localhost.run session gets a NEW random *.lhr.life subdomain. Any recovery that changes the URL silently invalidates listings-drafts.md citations unless the fresh URL is written somewhere bots read.
4. **PROVEN LIVE at 11:49–11:52 MDT:** CEO's listed origin `a157204d13d607.lhr.life` died within ~5 minutes of its 11:45 registration — tunnel had been relaunched (new ssh pid), new subdomain sat unrecorded in `/tmp/tunnel-8604.log` (the stderr target actually used by tunnel launches). Planner recovered the fresh URL from that file and re-registered (`listed:true`, verbatim in org/sales_log.md). This outage→orphaned-listing cycle WILL repeat every time anything relaunches the tunnel until this plan lands.

## STEPS
1. Record baseline: `echo -n "$(grep -o 'https://[a-z0-9]*\.lhr\.life' org/research/listings-drafts.md | head -1)" > docs/PUBLIC_URL.txt && cat docs/PUBLIC_URL.txt` (creates the pointer file if absent).
2. Edit `ops/watchdog.sh`: after existing service checks, add a public probe — read URL from docs/PUBLIC_URL.txt, `curl -sf -m 10 "$URL/health" >/dev/null || exit 1`. Watchdog exit 1 makes the existing ops-medic cron invoke medic.sh automatically (existing wiring, no cron changes).
3. Edit `ops/medic.sh`: add a `recover_tunnel()` block after the service restarts —
   - Probe `$URL/health`; if OK, return.
   - If local `http://127.0.0.1:8604/health` is DOWN, fix that first (existing restart handles it), then continue.
   - Else: `pkill -f 'ssh.*localhost.run'`; relaunch `ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:localhost:8604 nokey@localhost.run` with stdout/stderr to `/tmp/tunnel.log`.
   - Launch with stderr captured to `/tmp/tunnel-8604.log` (the established location — proven source of the current session's URL). Sleep 6; extract fresh URL via `grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/tunnel-8604.log | tail -1`; if non-empty, overwrite docs/PUBLIC_URL.txt (line 1) and `log "tunnel RECOVERED, url=$NEW"`; if URL CHANGED vs `$OLD`, also `sed -i "s|$OLD|$NEW|g" org/research/listings-drafts.md` and log the rotation to org/system_events.log.
4. Commit both scripts (`git add ops/watchdog.sh ops/medic.sh docs/PUBLIC_URL.txt && git commit -m "ops: DIR-025 tunnel supervision + URL pointer"`).
5. Drill A (tunnel): `pkill -f 'ssh.*localhost.run'`; wait for the next ops-medic cycle (≤15 min) OR run `bash ops/medic.sh` directly; then `curl -s -o /dev/null -w '%{http_code}\n' -m 15 "$(cat docs/PUBLIC_URL.txt)/health"` → expect **200**, and PUBLIC_URL.txt matches the live session.
6. Drill B (backend): stop :8604 (`pkill -f 'uvicorn .*--port 8604'`); `bash ops/watchdog.sh >/dev/null; echo $?` → expect **1**; `bash ops/medic.sh`; re-probe local health → 200.
7. Append drill evidence to this plan's EXECUTION section with real timestamps.

## VERIFY
- `bash ops/watchdog.sh` exits 1 when the public URL is broken and 0 when healthy.
- After Drill A: `curl -m 15 "$(cat docs/PUBLIC_URL.txt)/health"` → HTTP 200, file contents equal the live tunnel URL (`pgrep -af localhost.run` session still matching).
- After Drill B: :8604 `/health` → 200 within one medic pass.

## ROLLBACK
- `git revert` the single ops commit (or `git checkout HEAD~1 -- ops/watchdog.sh ops/medic.sh`); delete docs/PUBLIC_URL.txt. Existing :8604/:8605/:8610 restart logic is untouched by this plan and must remain working — verify with one `bash ops/watchdog.sh` healthy-run (exit 0) after rollback.

## ESTIMATED REVENUE IMPACT
Protective, not direct: Agent402's hourly probe marks sellers STALE on downtime and ranks by rolling crawl health — every minute of dead origin burns the only external discovery surface we have (and already cost one listing rejection today, DIR-024). Keeps catalog availability ≥98.5% (worst-case 14 min/15 min window vs current unbounded tunnel outages). Indirectly preserves the $0.01–$0.10/day channel-(b) pipeline.

## EXECUTION
(status=not-started — ops-medic fills in drill evidence here)
