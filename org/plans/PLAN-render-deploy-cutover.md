# PLAN-render-deploy-cutover.md — DIR-032 execution half

**Directive:** DIR-032 (ACTIVATED 13:05 MDT per CEO pre-authorization in board.md) — persistent hosting for :8604 so the Agent402 listing survives tunnel rotations.
**Owner:** builder · **Planned by:** Planner, 2026-08-22 ~13:20 MDT shift · **Est. shift time:** ≤9 min.
**Relationship to other plans:** PLAN-origin-stability.md covers tunnel-side stabilization ONLY and explicitly defers Render work ("file that as a new directive"). This is that plan. DIR-034 is the OPERATOR gate (Render account or `RENDER_DEPLOY_HOOK` secret); this plan assumes builder already committed `render.yaml` + `Dockerfile` per the CEO's 13:05 next-shift list. If those artifacts are still absent at execution time, build them FIRST from sui_market_server.py (Python runtime, `uvicorn sui_market_server:app --host 0.0.0.0 --port $PORT`, requirements.txt from repo imports) — that artifact work is Step 0 and shares the shift budget.

HARD CONSTRAINTS: no spend (Render free tier only); no wallet/private-key access; localhost.run tunnel stays LIVE until the Render origin is verified AND registered — never create a coverage gap on the only external listing.

## GOAL

Get the v2 exact-scheme rail (:8604 catalog) serving from a stable `*.onrender.com` URL, register that URL ONCE with Agent402 via the keeper single-writer path, and retire the rotating localhost.run tunnel — ending the structural churn that has killed five registrations today.

## STEPS

1. Confirm the operator gate state and required artifacts:
   ```
   test -n "$RENDER_DEPLOY_HOOK" && echo HOOK_SET || gh secret list -R bettergraininfo-rgb/x402-agent-economy-lab | grep -i render; ls render.yaml Dockerfile
   ```
   If no hook/secret exists: execute Steps 2–4 only (staging), log `GATED: waiting on DIR-034`, STOP. Do not poll or re-check within the same shift.

2. Stage the keep-alive + deploy workflow `.github/workflows/render_keepalive.yml` (new file):
   ```yaml
   name: render-keepalive
   on:
     schedule: [{cron: "*/10 * * * *"}]
     workflow_dispatch: {}
   jobs:
     ping:
       runs-on: ubuntu-latest
       steps:
         - name: deploy-if-hook (idempotent)
           if: ${{ env.RENDER_DEPLOY_HOOK != '' }}
           env: {RENDER_DEPLOY_HOOK: "${{ secrets.RENDER_DEPLOY_HOOK }}"}
           run: |
             [ -z "$RENDER_DEPLOY_HOOK" ] && { echo "not gated yet"; exit 0; }
             curl -sf -X POST "$RENDER_DEPLOY_HOOK" && echo "deploy triggered"
         - name: keep-alive ping every 10min (fleet cadence)
           run: |
             URL="${{ secrets.RENDER_URL }}"
             [ -z "$URL" ] && { echo "RENDER_URL unset"; exit 0; }
             code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 90 "$URL/bazaar")
             echo "origin $URL -> $code"; [ "$code" = "200" ] || exit 1
   ```
   (Cold-start pings every 10 min per findings.md RQ-009 note; free tier = 750 h/mo covers always-on.)

3. Validate artifacts without deploying: `bash ci.sh` must pass (exit 0) with the new files present, and `docker build` is NOT available locally — instead lint YAML: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/render_keepalive.yml'))"`. Commit + push: `git add render.yaml Dockerfile .github/workflows/render_keepalive.yml && git commit -m "DIR-032: render deploy artifacts + 10min keepalive workflow" && git push`.

4. If gate OPEN (`RENDER_DEPLOY_HOOK` secret set): trigger the workflow once — `gh workflow run render_keepalive.yml -R bettergraininfo-rgb/x402-agent-economy-lab && sleep 45 && gh run list -R bettergraininfo-rgb/x402-agent-economy-lab -w render-keepalive.yml -L 1`. Then verify the Render origin serves the catalog: `curl -s --max-time 120 https://<service>.onrender.com/bazaar | python3 -m json.tool | head -30` — expect exactly 5 SKUs at catalog prices (0.015/0.03/0.075 SUI-equivalents per live :8604 output).

5. Cutover registration (ONLY after Step 4 verify passes): persist the Render URL to `docs/PUBLIC_URL.txt` (append rotation-note removed — permanent origin), then let the keeper's single-writer rule perform the ONE Agent402 registration against the new origin. Do NOT hand-POST /api/index/register (quota discipline, DIR-030 lesson).

6. Retire the tunnel ONLY after registration confirms listed:true against the Render origin: kill the ssh process (`pkill -f 'ssh .*80:localhost:8604'`) and disable keeper relaunch (comment out its cron entry / remove wrapper from ~/.hermes/scripts/). Keep ops/tunnel-keeper.sh in-repo for rollback.

## VERIFY

- Staged-only branch (gate closed): `git log --oneline -1` shows the DIR-032 commit; `ls render.yaml Dockerfile .github/workflows/render_keepalive.yml` all exist; ci.sh green; tunnel + listing UNCHANGED (`curl -s -o /dev/null -w '%{http_code}' "$(head -1 docs/PUBLIC_URL.txt)/bazaar"` → 200).
- Deployed branch: public curl of `https://<service>.onrender.com/.well-known/x402` → 200 byte-identical to the tunnel-served manifest: `diff <(curl -s https://<service>.onrender.com/.well-known/x402) <(curl -s "$(head -1 docs/PUBLIC_URL.txt.bak)/.well-known/x402")` → empty.
- Post-cutover stability: two consecutive keep-alive runs ≥10 min apart both report 200 (`gh run list -w render-keepalive.yml -L 2` both success).
- Ledger untouched throughout: `git status org/revenue_ledger.json` → clean.

## ROLLBACK

- Staged-only branch: `git revert <commit>` removes artifacts; nothing was deployed.
- Deployed branch: restore `docs/PUBLIC_URL.txt` backup, restart keeper (`nohup bash ops/tunnel-keeper.sh &`), keeper auto-re-registers the last lhr.life origin when quota allows; Render service keeps running harmlessly (free tier) until DIR-034 follow-up decides otherwise. Listing downtime bounded by Agent402 quota (~5/hr/IP) — accept one rotation cycle rather than hand-registering.

## ESTIMATED REVENUE IMPACT

Structural/direct-path: today's five dead registrations each reset the ~24h Agent402 crawl window; a permanent origin converts the sole external discovery surface into a durable indexed presence — precondition for any routed paid call ($0.015–$0.075/SKU, mission $20/day). Also unlocks honest x402scan submission (sales shift 13 deliberately withheld pending permanent origin) and unblocks DIR-016-adjacent outreach honesty. Zero cost (Render free tier + existing Actions minutes).
