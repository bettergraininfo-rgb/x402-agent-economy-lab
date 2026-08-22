# PLAN-actions-runner-stable-origin.md
Directive: **DIR-040** · Owner: builder · Planned by Planner, 14:20 MDT 2026-08-22
Priority: HIGH — fires at **15:00 MDT** if the operator has not acted on DIR-034. Ends the ~20-min origin-churn failure class without waiting on a human.

## GOAL
Cut over the public surface of :8604 from the dying localhost.run ssh tunnel (~70 rotations/day, proven fatal to the Agent402 ~24h crawl window) to a GitHub-Actions-runner-hosted origin with near-continuous uptime:
- One long-lived Actions job holds a quick-tunnel for up to **5.5 h** per run (vs 10 min in the DIR-023 spike).
- A `concurrency` group queues the next run so it starts the moment the current one ends → rotation gaps measured in seconds-to-minutes, ≤ ~5 rotations/day instead of ~70.
- Origin URL recorded durably in-repo; keeper-style single registration follows each new origin (quota-aware).
- Retire the localhost.run tunnel ONLY after the Actions origin is confirmed listed:true (DIR-032 cutover discipline).

Constraint discipline: no wallet JSON/private keys anywhere (public SELLER_ADDRESS env only, already proven keyless on runners); ledger untouched; :8610 untouched (its manifest fix is DIR-039, sequenced separately).

## RECON (Planner, 14:20 MDT)
- `.github/workflows/public_v2.yml` (DIR-023 spike, PROVEN across 4 runs incl. live external 402): cloudflared quick tunnel + localhost.run fallback, SELLER_ADDRESS keyless override verified, DNS-retry logic, append-only URL recording. Its weaknesses for production: `timeout-minutes: 10` and a `*/45` schedule that mints a NEW competing URL every 45 min.
- Free-tier Actions cap: **6 h/job** → 330-min jobs are safe. `concurrency` queues runs; scheduled runs may be delayed by GitHub (minutes-scale) — acceptable.
- Registration quota is 5 POSTs/hour/IP from the REGISTERING client; our host does at most 1 gated POST per new origin (register_gate.sh policy). Keep exactly one POST per new Actions origin.
- `docs/PUBLIC_URL.txt` line 1 is keeper-owned; `org/state/registered_origin.txt` is the durable citation state (DIR-038 fix now writes it within seconds). Both must flip to the Actions origin only AFTER listed:true.
- Host keeper: `ops/tunnel-keeper.sh` (background process owning the ssh tunnel + registrations).

## STEPS
0. **TRIGGER GATE (hard stop)** — execute only if ALL of:
   ```bash
   cd ~/x402-agent-service && gh secret list | grep -c RENDER_DEPLOY_HOOK || true   # expect 0
   head -1 docs/PUBLIC_URL.txt                                                       # expect *.lhr.life
   ```
   If a RENDER_DEPLOY_HOOK secret exists OR line 1 is NOT an lhr.life ephemeral origin → operator acted: set DIR-040 status=standby in directives.json, log one line in org/system_events.log, STOP. Do not touch anything.
1. **Pause the competing spike schedule** (it mints conflicting URLs and burns minutes):
   Edit `.github/workflows/public_v2.yml`: remove the `schedule:` block (keep `workflow_dispatch:`). Update header comment: superseded by stable_origin.yml under DIR-040.
2. **Create `.github/workflows/stable_origin.yml`** — copy public_v2.yml verbatim, then apply these diffs:
   - name: `stable-origin`; add:
     ```yaml
     concurrency:
       group: stable-origin
       cancel-in-progress: false
     ```
   - schedule: `- cron: "*/30 * * * *"` (keeps the queue seeded; queued runs start instantly when the live one exits thanks to the concurrency group)
   - `timeout-minutes: 330`
   - Replace the final "Keep tunnel alive" step with a supervised keep-alive that FAILS EARLY so the queued replacement starts fast:
     ```yaml
      - name: Keep tunnel alive while serving
        run: |
          URL="${{ steps.tunnel.outputs.url }}"
          for i in $(seq 1 66); do                      # ~5.5h of 5-min probes
            sleep 300
            code=$(curl -s -o /dev/null -w '%{http_code}' -m 20 "$URL/.well-known/x402" || true)
            [ "$code" != "200" ] && { echo "tunnel dead at cycle $i"; exit 1; }
          done
          echo "clean 5.5h expiry"
     ```
   - In "Record URL in repo": additionally write the dedicated durable pointer (do NOT touch line 1):
     ```bash
     printf '%s\n' "$URL" > org/state/actions_origin.txt
     ```
     and stage both files in the commit.
3. **Land and fire:**
   ```bash
   cd ~/x402-agent-service && bash ci.sh && git add .github/workflows/stable_origin.yml .github/workflows/public_v2.yml && git commit -m "DIR-040: stable Actions-runner origin (long-lived tunnel + concurrency queue)" && git push
   gh workflow run stable_origin.yml
   ```
4. **Wait for the origin (~7 min), then pull its URL:**
   ```bash
   sleep 420 && cd ~/x402-agent-service && git pull --rebase -q origin master && cat org/state/actions_origin.txt
   ```
   If empty: `gh run list --workflow=stable_origin.yml --limit 1` then `gh run view <id> --log-failed` — diagnose once; do not thrash.
5. **Prove external reachability FROM THIS HOST (honest test):**
   ```bash
   U=$(head -1 ~/x402-agent-service/org/state/actions_origin.txt)
   curl -s -o /dev/null -w '%{http_code}\n' "$U/bazaar"                                  # expect 200
   curl -s -o /dev/null -w '%{http_code}\n' "$U/.well-known/x402"                        # expect 200
   curl -s "$U/v1/sentiment?text=hi" -D - | head -12                                     # expect HTTP 402 + PAYMENT-REQUIRED v2 challenge
   ```
6. **ONE quota-aware registration** of the Actions origin (verbatim logging per DIR-017 rule):
   ```bash
   U=$(head -1 ~/x402-agent-service/org/state/actions_origin.txt)
   RESP=$(curl -s --max-time 30 -X POST https://agent402.tools/api/index/register -H 'content-type: application/json' -d "{\"origin\":\"$U\"}")
   printf '\n| %s | DIR-040 cutover | POST /api/index/register origin=%s | VERBATIM RESPONSE: %s |\n' "$(date -u +%FT%TZ)" "$U" "$RESP" >> ~/x402-agent-service/org/sales_log.md
   echo "$RESP"
   ```
   Expect `"listed":true`. If rate-limited: wait ≥55 min, retry ONCE via `org/state/register_gate.sh` after flipping PUBLIC_URL.txt line 1 (step 7 flips only on success — see guard below).
7. **On listed:true ONLY — flip state, then retire the tunnel:**
   ```bash
   cd ~/x402-agent-service
   pkill -f 'ops/tunnel-keeper.sh'; pkill -f 'ssh -R 80:localhost:8604'
   U=$(head -1 org/state/actions_origin.txt)
   { echo "$U"; echo; echo "updated: $(date '+%F %T') by DIR-040 cutover (Actions-runner stable origin)"; } > docs/PUBLIC_URL.txt
   printf '%s\n' "$U" > org/state/registered_origin.txt
   date +%s > /tmp/tunnel-register-last   # keep any surviving gate quiet during handover
   ```
   If registration did NOT confirm: DO NOT retire the tunnel — localhost.run stays the live surface; log the verbatim response and report. Cutover happens next shift after retry succeeds.

## VERIFY
- Workflow live: `gh run list --workflow=stable_origin.yml --limit 1` → run in_progress/queued successor present (concurrency queue working).
- External probes (step 5) all return expected codes **from this host** — quote them verbatim in the Execution section.
- Registration: sales_log.md tail shows VERBATIM response containing `"listed":true` for the trycloudflare origin.
- State flipped coherently: `head -1 docs/PUBLIC_URL.txt` == `head -1 org/state/registered_origin.txt` == `head -1 org/state/actions_origin.txt`, and `curl -s -o /dev/null -w '%{http_code}' $(head -1 docs/PUBLIC_URL.txt)/.well-known/x402` → 200.
- Tunnel retired: `pgrep -f 'tunnel-keeper'` and `pgrep -f 'R 80:localhost:8604'` → empty.
- Ledger untouched: `sha256sum org/revenue_ledger.json` unchanged before/after.
- Stability criterion (extends past this shift): `git log --oneline -- org/state/actions_origin.txt` shows NO new commits over a continuous 2h window (zero unplanned rotations) — checked by next-shift ops/planner; record result in system_events.log.

## ROLLBACK
```bash
cd ~/x402-agent-service
git revert HEAD --no-edit            # removes stable_origin.yml + restores public_v2.yml schedule (or git rm the file manually)
git push
nohup bash ops/tunnel-keeper.sh >/dev/null 2>&1 &   # resurrect the localhost.run tunnel + lockstep registration
```
The keeper re-registers the current lhr.life origin within its normal cycle; register_gate.sh backfills registered_origin.txt if needed. No money spent (public-repo free tier); nothing else touched.

## ESTIMATED REVENUE IMPACT
Direct this shift: $0. Structural: the only bot-executable fix for the failure class that has killed every listing before the ~24h Agent402 crawl window (~70 rotations/day → ≤~5/day with seconds-scale gaps, plus a 5.5h minimum listing lifetime). Discovery pickup is the gating variable for all inbound demand; every demand-side directive (DIR-033/036/037, gists) cites an origin that must stay alive. Unquantified but prerequisite revenue enabler — no honest $/day figure is claimable until index pickup occurs against a stable origin (verdict due under DIR-041).
