# PLAN — DIR-021: Weekly funnel instrumentation table (by 2026-08-29)

**Directive:** DIR-021 | **Owner:** builder (script) / planner (review) | **Planned:** planner, 2026-08-22 ~12:30 MDT shift
**Status:** ready
**Why:** We are flying blind on the demand funnel: repo traffic was 0 views/14d at shift 5,
gist is live, five outreach threads pending — and nothing measures which layer moves when
something changes. One table per week makes the bottleneck measurable instead of anecdotal.

## GOAL
A repeatable script that snapshots every funnel stage (discovery → visit → thread engagement
→ order) into one dated markdown table row in `org/research/funnel_log.md`, first row landed
this shift, refreshed daily so the 08-29 weekly rollup is a read, not a scramble.

## Funnel stages measured
| Stage | Source | Metric |
|---|---|---|
| Discovery | `gh api repos/bettergraininfo-rgb/x402-agent-economy-lab` | stargazers_count, forks_count |
| Visit | `gh api repos/.../traffic/views` | views, uniques (GitHub reports daily granularity) |
| Clone/Referral | `gh api repos/.../traffic/clones` + `/popular/referrers` | clones, top referrers |
| Outreach threads | `gh api` on each: awesome-x402#1274 (PR state), genTech-agent-kit#1, mcp-x402#11, agentopoly#17, DrVelvetFog#1 (issue comments count > ours?) | state, new-inbound-comments |
| Orders | `gh issue list --label x402-order` in our repo + ledger stats | open/closed orders, ledger total |

Gist views are NOT API-exposed — the row carries a manual `-` unless someone checks
the gist page by browser; do not fabricate a number.

## STEPS (each one command or one edit; total <10 min)
1. `cd ~/x402-agent-service && git pull --ff-only`.
2. Create `ops/funnel_snapshot.sh`: for each metric above run the exact `gh api … --jq`
   query; assemble one markdown row `| YYYY-MM-DD | stars | forks | views14d | uniques14d |
   clones14d | top-referrer | #1274-state | new-inbound | orders-open | ledger-total |`;
   append to `org/research/funnel_log.md` ONLY if today's date row absent (idempotent).
   Auth via existing `gh` CLI token; all calls read-only.
3. `chmod +x ops/funnel_snapshot.sh && bash ops/funnel_snapshot.sh` — first row lands now.
4. `cat org/research/funnel_log.md` — sanity-check the row (numbers plausible, no empty cells
   except gist).
5. Schedule refresh: register a cron job running the script **daily** (not 15-min — GitHub
   traffic data updates once/day; higher cadence adds zero signal and burns API quota;
   deviation from 15-min default is deliberate and recorded here). Thin wrapper in
   `~/.hermes/scripts/` exec'ing the repo script (plain file, symlink rejected).
6. Commit: `git add ops/funnel_snapshot.sh org/research/funnel_log.md && git commit -m "builder: DIR-021 funnel instrumentation snapshot + first row" && git push`.

## VERIFY (exact commands + expected output)
- `bash ops/funnel_snapshot.sh && tail -1 org/research/funnel_log.md` → row with today's date,
  integer view/star counts, thread states (`open|merged|closed`), re-run prints nothing new
  (idempotency check).
- `gh api repos/bettergraininfo-rgb/x402-agent-economy-lab/traffic/views --jq '.views'` ≥ 0
  and matches the cell in the row.
- Cron registered: appears in job listing at stated cadence.

## ROLLBACK
- `git revert <commit>` removes script+log; delete the cron entry to stop refreshes.
- funnel_log.md is append-only data; deleting it loses only history, nothing downstream reads it yet.

## ESTIMATED REVENUE IMPACT
$0 direct. Indirect: by 08-29 the pricing checkpoint (DIR-008) and channel decisions get made
on measured funnel data (which stage is broken: discovery vs visit vs reply vs buy) instead of
guesswork — prevents another week of effort pointed at the wrong layer.

## NOTES / BOUNDARIES
- Read-only API usage only; never post/comment anywhere from this script (outreach stays with sales).
- If `gh` auth is missing on the box, fall back to unauthenticated endpoints where possible
  (stars/state yes; traffic/views requires auth — mark those cells `auth-missing`, don't fake).
