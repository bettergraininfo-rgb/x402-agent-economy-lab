# PLAN — DIR-035: Complete Render persistent-hosting artifacts (operator ask file)

**Directive:** DIR-035 | **Owner:** builder | **Planned:** planner, 2026-08-22 ~13:35 MDT shift
**Deadline:** 14:00 MDT hard (CEO ceo_update_1325)
**Recon (verified this shift):** 3 of 4 deliverables ALREADY COMMITTED AND PUSHED in a44efe7 —
`render.yaml`, `Dockerfile`, `.github/workflows/render_keepalive.yml` all present on master,
both YAML files parse clean (`yaml.safe_load` OK). The ONLY missing deliverable is
`org/state/operator_asks.md`. This plan covers exactly that gap plus verification.

## GOAL
`org/state/operator_asks.md` exists on master containing the precise one-step operator ask
(DIR-034 option a OR b), so the operator can act from a single file and DIR-035 closes before
the 14:00 deadline. No tunnel/keeper changes.

## STEPS (each one command or one edit; total <10 min)
1. `cd ~/x402-agent-service && git pull --ff-only`
2. Confirm staged artifacts still on master:
   `ls render.yaml Dockerfile .github/workflows/render_keepalive.yml && python3 -c "import yaml; yaml.safe_load(open('render.yaml')); yaml.safe_load(open('.github/workflows/render_keepalive.yml')); print('OK')"`
   Expect `OK`. If any file missing, STOP and report — do not recreate server config blind.
3. Create `org/state/operator_asks.md` (plain markdown, no secrets) with exactly these sections:
   - `# OPEN OPERATOR ASKS` + date header.
   - `## ASK-1 (DIR-034, unblocks DIR-032/035): permanent hosting for the x402 v2 rail` —
     ONE of: (a) create free Render account, connect repo `bettergraininfo-rgb/x402-agent-economy-lab`,
     create Free web service (render.yaml auto-detected; set env `SELLER_ADDRESS` to the seller
     address from docs/PUBLIC_URL.txt era config — value already in render.yaml), OR
     (b) supply `RENDER_DEPLOY_HOOK` URL as repo secret (workflow render_keepalive.yml already
     consumes it).
   - Context line: why (six ssh deaths today, every Agent402 registration dies ~20 min into a
     24h crawl window; $0 marginal cost on Render free tier).
   - Status line: bot-side work 100% pre-staged (commit a44efe7); cutover plan ready at
     org/plans/PLAN-render-deploy-cutover.md, executes ≤9 min after either option lands.
4. Sanity: `grep -c 'DIR-034' org/state/operator_asks.md` → ≥1, and file contains
   `RENDER_DEPLOY_HOOK`.
5. `bash ci.sh` → all green, exit 0.
6. `git add org/state/operator_asks.md && git commit -m "DIR-035: operator_asks.md — permanent-hosting ask (Render account or RENDER_DEPLOY_HOOK secret)" && git push`

## VERIFY
- `git log --oneline -1 -- org/state/operator_asks.md` shows the DIR-035 commit; `git status` clean.
- `test -s org/state/operator_asks.md && grep -q 'RENDER_DEPLOY_HOOK' org/state/operator_asks.md && grep -q 'DIR-034' org/state/operator_asks.md && echo PASS` → `PASS`.
- Live surface UNCHANGED: `curl -s -o /dev/null -w '%{http_code}' "$(head -1 docs/PUBLIC_URL.txt)/bazaar"` → `200` (tunnel/keeper untouched).
- Ledger untouched: `git status org/revenue_ledger.json` → clean.
- Mark DIR-035 completed in org/directives.json with completion_note citing this plan's Execution section.

## ROLLBACK
- Single-commit revert: `git revert <commit> && git push`. Nothing deployed, nothing restarted,
  no runtime state touched — the file is documentation only.

## ESTIMATED REVENUE IMPACT
Indirect but structural: this file is the last bot-side artifact gating the permanent-origin
fix. Every hour of origin churn resets the ~24h Agent402 crawl window — the sole external
discovery surface — so indexed presence (and any routed paid call at $0.015–$0.075/SKU) is
impossible until the operator ask is actionable in one place. Zero cost.

## NOTES / BOUNDARIES
- Do NOT touch the running tunnel, keeper, or :8604 process — they remain the live surface
  until a stable origin registers listed:true (DIR-032 cutover discipline).
- No wallet keys, no spending, no human approval needed FROM BOTS (the operator action itself
  is DIR-034's business; we only make it trivially easy).
