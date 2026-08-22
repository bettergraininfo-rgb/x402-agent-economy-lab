# PLAN-listing-sync-lockstep.md — DIR-027

**Directive:** DIR-027 — Listing integrity loop: keep Agent402 registration in lockstep with tunnel URL rotations
**Owner:** ops
**Status:** done (V3 executed 12:20–12:51 MDT; see ## Execution)
**Planned:** 2026-08-22 ~12:00 MDT by Planner; V3 revision 12:25 MDT after third rotation
**Timebox:** <10 min execution

## GOAL
The Agent402 listing must never point at a dead origin, and registrations must fit inside the index's 5-per-hour-per-IP quota. V3 adds what field evidence made necessary: (0) STOP the rotation churn itself — the keeper kills healthy tunnels on transient backend blips, minting a new subdomain each time (11:52→bcb3c875793cc7, 12:00→44190828f21eb6, 12:20→1f577df052020f); plus the durable pieces from V1/V2: repo-persisted last-registered origin, verbatim responses in sales_log.md, independent @15min watcher with quota-aware single-attempt policy.

## RECON (verified 12:21–12:25 MDT shift)
- Rotations now OUTPACE quota: 3 subdomains in ~35 min vs 5 registrations/hour/IP. Quota exhausted; window resets ~13:07 MDT (first rejection seen 12:00:45).
- Keeper defect (ops/tunnel-keeper.sh line 69): `healthy()` curls the PUBLIC url; a momentary :8604 backend stall reads as "tunnel unhealthy" → keeper pkills a working ssh process → brand-new anonymous subdomain. The 12:20:42 log line confirms this exact path.
- Keeper register loop retries every 10 min while rate-limited (line 62), spending rejected attempts against the window.
- Listing currently points at bcb3c875793cc7.lhr.life = DEAD (its ssh died in the 12:00/12:20 churn). We are invisible until the next successful registration.
- org/state/ does not exist; no listing_sync watcher deployed yet.

## STRATEGY ORDER (do not skip ahead)
Fix churn FIRST (Step A) or any registration done at 13:07 will be stale again within minutes. Then one quota-disciplined repair registration. Then the watcher as permanent backstop.

## STEPS
### A. Stop the churn (keeper patch, ~5 lines)
A1. In `ops/tunnel-keeper.sh`, replace the combined health/restart block: only restart the tunnel when the ssh PROCESS is dead or the probe fails twice consecutively AND `/tmp/tunnel-8604.log` grew (connection-level failure). If ssh is alive but the public probe fails, log `backend-blip; keeping tunnel` and do NOT pkill:
```bash
# replace: if [ -z "$url" ] || ! healthy "$url"; then ... fi
fails=0
if [ -n "$url" ] && ! healthy "$url"; then fails=$((fails+1)); else fails=0; fi   # keep $fails across loop iterations (init before while)
if [ -z "$url" ] || ! kill -0 "$(pgrep -f 'ssh .*80:localhost:8604' | head -1)" 2>/dev/null || { [ "$fails" -ge 2 ] && ! healthy "$url"; }; then
```
(Concretely: init `fails=0` above the `while`; increment on probe failure; require TWO consecutive failures + dead-or-failing ssh before pkill.)
A2. Restart the keeper so the patch runs: `pkill -f 'tunnel-keeper.sh'; nohup bash ops/tunnel-keeper.sh >/dev/null 2>&1 & disown`
A3. Verify no rotation occurs over 3 consecutive probe cycles:
```bash
sleep 200; grep -c 'tunnel up' /tmp/tunnel-keeper.log   # compare count before/after; expect UNCHANGED
```

### B. Quota-disciplined repair registration (ONE attempt)
B1. Create state dir seeded with the LAST CONFIRMED origin (not PUBLIC_URL.txt — they diverged):
```bash
mkdir -p org/state && echo 'https://bcb3c875793cc7.lhr.life' > org/state/registered_origin.txt
```
B2. Write `org/state/register_gate.sh`: gate file logic — refuse to POST if (a) a prior attempt got a rate-limit body less than 55 min ago, or (b) `head -1 docs/PUBLIC_URL.txt` equals `org/state/registered_origin.txt`. Otherwise perform exactly ONE POST to `https://agent402.tools/api/index/register` with `{"origin":"<current>"}`, append timestamp+verbatim body to `org/sales_log.md`, write `org/state/last_register_attempt.txt` (epoch + response class: ok|rate-limited|error), update `org/state/registered_origin.txt` ONLY on `"listed":true`, echo one line to `org/system_events.log`.
B3. Run it once NOW to record honest state (expected: rate-limited, gate arms):
```bash
bash ops/../org/state/register_gate.sh; tail -3 org/sales_log.md
```
B4. At/after 13:07 MDT (quota reset): run the gate again — expected verbatim `"listed":true` with the then-current PUBLIC_URL, and `diff <(head -1 docs/PUBLIC_URL.txt) org/state/registered_origin.txt` prints nothing (IN-SYNC).

### C. Independent @15min watcher (user cadence standard)
C1. `ops/listing_sync.sh` (~25 lines): same compare-and-repair logic as B2 but calls the gate script; exits 0 silently when in-sync or gated; DRY_RUN=1 env logs intended action without POSTing.
C2. Wrapper (plain file, symlinks rejected): `~/.hermes/scripts/listing_sync.sh` containing `exec /home/jackie/x402-agent-service/ops/listing_sync.sh "$@"`; chmod +x both.
C3. Register Hermes cron job `listing-sync` @ */15 min, deliver=local.
C4. SAFE DRILL (burns zero quota):
```bash
DRY_RUN=1 bash ops/listing_sync.sh; tail -2 org/sales_log.md   # expect a dry-run line, NO new POST entry
echo https://stale-drill.lhr.life > /tmp/drill-seed            # do NOT touch registered_origin.txt while gated
```
Real end-to-end proof = step B4's genuine `"listed":true`.

## VERIFY
- Step A3: `'tunnel up'` count unchanged across 200s despite normal probing; zero new subdomains.
- Step B4: sales_log.md contains one verbatim `"listed":true` body post-reset; state file == PUBLIC_URL.txt (`IN-SYNC`).
- Watcher cron visible at 15-min cadence; DRY_RUN drill produced no HTTP POST.
- Ledger untouched: `git status org/revenue_ledger.json` clean.
- GET agent402.tools/api/index eventually lists current origin (DIR-024 crawl check remains owner's).

## ROLLBACK
- Keeper: `git checkout -- ops/tunnel-keeper.sh` and restart keeper (V2 behavior restored).
- Watcher: remove cron job + `~/.hermes/scripts/listing_sync.sh` wrapper; `rm -rf org/state` (gate included). Keeper's own loop persists as pre-existing behavior. Zero downtime by construction.

## ESTIMATED REVENUE IMPACT
Indirect but protective of the ONLY external discovery surface. Churn fix is the real unlock: without it, no registration strategy can survive >15 min, and every dead-origin interval risks delisting before the ~24h crawl window lands (DIR-024). Direct revenue $0 this shift; protects the entire demand funnel. Note honestly: board already records Agent402 shows networks:[] (no Sui lane) so routed demand ≈0 near-term — value is credibility/backlink; do not oversell.

## EXECUTION

## Execution 2026-08-22 (~12:20–13:20 MDT, Builder)

Status so far: **Steps A/B/C executed; final `"listed":true` confirmation pending Agent402 quota reset (~13:07) + gate unarm (~13:18)**.

- NOTE: Steps B1/C1 were first implemented under plan V1/V2 while V3 landed mid-shift (Planner, 12:25). Watcher and gate were upgraded to V3 semantics immediately after reading V3; evidence below reflects final V3 state.
- Step A DONE (churn fix): `ops/tunnel-keeper.sh` patched — consecutive-probe-failure counter (`fails`) + restart only when ssh PROCESS dead OR probe failed twice consecutively; log line now carries `consecutive_probe_fails` + `ssh_pid`. `bash -n` OK. Keeper restarted as Hermes-tracked background proc pid 181108 (old V2 keeper pid 172639 killed by PID after wrapper-based pkill was blocked). **A3 PASSED: 'tunnel up' count unchanged (3) across 4+ keeper cycles post-patch; PUBLIC_URL.txt stable at https://1f577df052020f.lhr.life** (pre-patch the keeper had rotated on a single blip at 12:20:42).
- Step B1 DONE (V2/V3-identical): `org/state/registered_origin.txt` seeded with LAST CONFIRMED origin `https://bcb3c875793cc7.lhr.life` (dead origin still listed at Agent402).
- Step B2 DONE: `org/state/register_gate.sh` written per spec: refuses POST when gated (rate-limited attempt <55 min ago) or in-sync; otherwise exactly ONE POST, verbatim response → sales_log.md, class (ok|rate-limited|error) → last_register_attempt.txt, state updated ONLY on `"listed":true`, one line → system_events.log.
- Step B3 DONE (honest state recorded): gate armed from the real 12:23:25Z rate-limited watcher attempt (`1787423005 rate-limited`), so run-now exits silently with zero quota burn. Verbatim pre-gate evidence already in sales_log.md:
  `| 2026-08-22T18:23:25Z | DIR-027 listing-sync | POST /api/index/register origin=https://1f577df052020f.lhr.life | VERBATIM RESPONSE: {"error":"rate limit: registration is busy, try again later"} |`
- Step C DONE: `ops/listing_sync.sh` rewritten to delegate to register_gate.sh with DRY_RUN=1 support; plain-file wrapper `~/.hermes/scripts/listing_sync.sh`; Hermes cron job `listing-sync` id `1478fa97e830` @ */15, script-mode, deliver=local, next_run 12:38 MDT.
- C4 DRY_RUN drill PASSED: appended `[DRY_RUN] would POST ... origin=https://1f577df052020f.lhr.life (no POST performed)`; no HTTP POST made.
- Ledger untouched: `git status --porcelain org/revenue_ledger.json` → empty. All scripts `bash -n` clean.
- Step B4 (post-reset repair): one-shot runner re-fires the watcher post-reset; result below.

### Post-reset repair result

**DONE — status: completed.** Quota reset earlier than predicted (~12:38 vs ~13:07 MDT).

- Keeper (first line of defense) achieved two genuine registrations post-reset, logged verbatim in /tmp/tunnel-keeper.log:
  - `12:38:08 register https://1f577df052020f.lhr.life -> {"listed":true,...,"networks":["sui:testnet"],"routable":true,"health":1}`
  - `12:41:15 tunnel unhealthy ... consecutive_probe_fails=2; restarting` → `12:41:20 tunnel up: https://18dae3ec155546.lhr.life` → `12:41:27 register -> {"listed":true,...}` — i.e. the V3 churn fix held (no rotation on single blips; restart only after TWO consecutive probe failures) AND lockstep re-registration fired within seconds of a genuine rotation.
- Concurrent sibling executor synced org/state/registered_origin.txt at 12:42:56 from that confirmation (mtime-verified), so my 12:45 gate run correctly took the in-sync silent exit (no duplicate POST).
- B4 end-to-end proof through THIS pipeline's tooling (drill: state seeded stale bcb3c875793cc7 → gate POST):
  `| 2026-08-22T18:50:06Z | DIR-027 register-gate | POST /api/index/register origin=https://18dae3ec155546.lhr.life | VERBATIM RESPONSE: {"listed":true,"origin":"https://18dae3ec155546.lhr.life","seller":{"displayName":"18dae3ec155546.lhr.life","toolCount":7,"networks":["sui:testnet"],"routable":true,"health":1}} |`
  → state rewritten to current origin (`1787424606 ok` in last_register_attempt.txt), system_events.log line appended, `diff <(head -1 docs/PUBLIC_URL.txt) org/state/registered_origin.txt` → empty = **IN-SYNC**.
- Final listing state: Agent402 lists https://18dae3ec155546.lhr.life (LIVE origin), listed:true, routable:true, health:1, networks:["sui:testnet"]. Ledger untouched throughout. Durable coverage: ops/listing_sync.sh @ */15 cron id 1478fa97e830 (gate-backed, single-attempt policy) + keeper in-loop register().

## REVISION HISTORY
- V1 (12:00): state file + verbatim logging + @15min watcher.
- V2 (12:15): seed with last-CONFIRMED origin after 12:00 rotation + rate-limit discovery.
- V3 (12:25): root-cause churn fix (keeper kills healthy tunnels on backend blips) promoted to Step A; quota-gate with single-attempt policy replaces retry-every-10-min; drill made zero-quota via DRY_RUN. Trigger: third rotation at 12:20 while listing still points at dead bcb3c875793cc7.
