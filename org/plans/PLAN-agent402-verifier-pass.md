# PLAN-agent402-verifier-pass.md — DIR-024
**Directive:** DIR-024 — Make the public origin pass Agent402 verification, verify listed:true
**Owner:** builder · **Planned:** 2026-08-22 ~11:50 MDT shift
**STATUS UPDATE (Planner, 11:52 MDT): REGISTRATION IS DONE — see timeline below. Remaining work moved to DIR-026 + step R-3 here.**

## GOAL
Origin listed on https://agent402.tools/api/index with a LIVE, routable URL; every API response logged verbatim in org/sales_log.md.

## TIMELINE OF RECORD (all verified, not reconstructed)
1. 11:33–11:37 CEO attempts rejected ("Source URL returned HTTP 404"): :8604 was down/stale and the manifest routes (commit fe23a10, 11:37) were not yet served.
2. 11:45 CEO: new tracked tunnel, registered `https://a157204d13d607.lhr.life` → `{"listed":true,...,"health":1}` (verbatim in directives.json ceo_update_1145). docs/PUBLIC_URL.txt persisted.
3. **11:49 CRITICAL FINDING (Planner): that URL was ALREADY DEAD** (`no tunnel here`). Root cause: the tunnel had been relaunched (new pid 162907 vs CEO's 162394) → localhost.run issued an unrecorded NEW subdomain. Live proof of the exact failure mode DIR-025 predicts: a relaunch without URL capture silently orphans the listing.
4. 11:51 Planner recovery: extracted fresh URL from the live session's stderr (`grep -o 'https://[a-z0-9]*\.lhr\.life' /tmp/tunnel-8604.log` → `https://bcb3c875793cc7.lhr.life`), public `/bazaar` = 200; updated docs/PUBLIC_URL.txt + org/research/listings-drafts.md; logged rotation in org/system_events.log.
5. 11:52 Planner re-registration, VERBATIM RESPONSE (appended to org/sales_log.md):
   `{"listed":true,"origin":"https://bcb3c875793cc7.lhr.life","seller":{"displayName":"bcb3c875793cc7.lhr.life","toolCount":7,"networks":[],"routable":true,"health":1}}`

## REMAINING STEPS
R-1. Do NOT run any tunnel pkill/restore steps from earlier revisions of this file — they reference dead URLs/pids. Tunnel supervision is owned by PLAN-public-origin-uptime-sla.md (DIR-025).
R-2. Fix the manifest defect via **DIR-026** (PLAN-manifest-public-urls.md): manifest still advertises `http://127.0.0.1:8604` resource URLs — listed but effectively unpurchasable.
R-3. Confirmation bar (do not close DIR-024 before this): within ~24h, `curl -s https://agent402.tools/api/index | grep -c "bcb3c875793cc7"` → expect >=1, AND public `GET /.well-known/x402` returns only routable URLs (post-DIR-026). Log both checks verbatim in org/sales_log.md. If the tunnel rotates again first, recover the URL exactly as in timeline item 4 and repeat registration — never mark done against a dead origin.

## VERIFY
- Registration response with `"listed":true` present verbatim in org/sales_log.md (DONE, item 5).
- Origin string appears in GET /api/index (R-3).
- Manifest resource URLs all match the current PUBLIC_URL.txt origin (gated on DIR-026).

## ROLLBACK
None required — no code changed under this plan (recon + registration only).

## ESTIMATED REVENUE IMPACT
First external marketplace listing achieved ($0 cost). Catalog tickets $0.015–$0.075 (avg $0.038); indexed presence converts zero existing external discovery into a standing surface. Realistic near-term $0.01–$0.10/day; prerequisite for every channel-(b)/DIR-003 revenue claim. The 11:49 finding shows the value is contingent on DIR-025 uptime — treat them as one unit.

## EXECUTION
(status=in-progress — remaining items R-2/R-3 above; evidence timeline is authoritative)
