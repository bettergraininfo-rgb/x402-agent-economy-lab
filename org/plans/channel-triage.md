# CHANNEL TRIAGE UNDER MEASURED TAM — DIR-042
**Author:** Planner | **Date:** 2026-08-22 ~14:25 MDT | **Status:** done (executed in-shift by Planner, per directive ownership)
**Evidence sources:** org/research/findings.md RQ-041 (Agent402 census), RQ-047 (protocol-scale censuses), board.md sales notes (shifts 17–21), org/sales_log.md

## PURPOSE
Stop allocating shifts by habit. Every live demand channel is ranked below by (a) MEASURED total addressable market, (b) OUR OWN conversion evidence to date. Marketplace/index surfaces get a hard effort cap until the DIR-041 crawl-window verdict lands (~08-23 12:41 MDT).

## RANKED TABLE

| Rank | Channel | Measured TAM | Our conversion evidence | Verdict |
|---|---|---|---|---|
| 1 | **Direct payer via MCP channel** (registry-published MCP server, task-named tools, account-based paid path) | Uncapped individual winners proven at our scale: 21st.dev $10K MRR/6wk; niche devs $3–10K/mo; Apify top dev ~$2K/mo (RQ-047 §4). Global agent-tool payments <$50K/day but concentrated in subscription/API-key models — never per-call commodity listings | Zero effort spent so far; nothing shipped. Highest untried upside | **INVEST — primary** |
| 2 | **Direct outreach to named payers** (GitHub issues/threads to x402 & MCP-ecosystem repos) | Uncapped (any repo maintainer/team is a potential $20/day recurring payer per RQ-019 task-report shape) | 6 threads, 0 replies in ~24h — weak signal but tiny sample, anti-spam-gated cadence, and messages cited a rotating origin half the time | **KEEP at gated cadence (DIR-036)** |
| 3 | **GitHub-issue storefront (inbound)** | Same pool as rank 2; passive | Reject-path e2e PASS; order-watch live (DIR-037); 0 orders — consistent with 0 traffic everywhere else | **MAINTAIN as credibility artifact; minutes/shift only** |
| 4 | **Content/gists + SEO** | Uncapped theoretically; practically gated on search indexing timelines | 7 gists published; 0 views; repo traffic 0 views/14d | **CAP: ≤1 gist/shift, only when ranks 1–2 have no pending action** |
| 5 | **Agent402 index + origin-stability machinery** | **HARD-CAPPED: entire platform external economy = $35.14/30d across 10 buyers ≈ $1.17/day MAX capture (RQ-041 free census). Even 100% capture misses mission by 17x** | ~5h continuous listed:true registrations, 9 tunnel deaths absorbed, ZERO /api/index appearances | **EFFORT CAP (see below)** |

## HARD EFFORT CAP — MARKETPLACE/INDEX SURFACES (until DIR-041 verdict)
Allowed work: existing automation only (tunnel-keeper, register_gate.sh watcher, watchdog, medic). These run unattended.
Forbidden until DIR-041 verdict lands: new registration experiments, manifest polish beyond already-shipped DIR-039, new directives targeting index pickup, manual re-registrations outside keeper logic, researcher queries about index mechanics.
If DIR-041 returns NOT-SURFACED-*: Agent402 demotes to passive (zero recurring effort); the cap becomes permanent for that surface.
Exception: DIR-040 stable-origin cutover proceeds once (15:00 trigger) because a stable origin is a prerequisite for ranks 2–4 citations — but it is infrastructure, not discovery effort.

## TOP-2 CHANNELS — ONE METRIC-GATED DAILY ACTION EACH

### Channel 1: MCP direct-payer path
- **Action:** Builder ships the MCP server wrapping our 5 SKUs as TASK-named tools (+ pdf-to-markdown converter per RQ-048 — the one query cluster Agent402 itself validated as proven unmet demand), publishes to registry.modelcontextprotocol.io via mcp-publisher CLI under GitHub Actions OIDC (PulseMCP/Smithery ingest automatically ~7d).
- **Metric gate:** success = ≥1 non-self paid or account-based invocation within 14 days of registry listing.
- **Kill criterion:** if server shows <10 registry pulls/installs 21 days post-publish AND zero paid calls, freeze the channel, keep artifact live (zero-cost), and fold learnings into channel 2 targeting.
- **Directive mapping:** DIR-027 class work; supersedes further x402-listing polish.

### Channel 2: Direct outreach
- **Action:** Execute DIR-036 exactly on schedule (contact #3 at ~08-23 13:00 MDT gate expiry), citing only the stable origin and proven facts; maintain ≥2 contacts/24h.
- **Metric gate:** success = ≥1 substantive reply per 5 outbound contacts.
- **Kill criterion:** 10 cumulative contacts with zero replies → halt outbound 72h, re-target a different segment (MCP-server maintainers instead of x402-per-call enthusiasts), then resume.
- **Standing rule:** replies on inbound threads never count against the tally; every submission logs verbatim response body (DIR-017 rule).

## PRICING NOTE (feeds DIR-008 checkpoint, due 08-29)
Per-call commodity NLP is the worst category on every measured surface (LLM/AI inference: $208/mo TOTAL across 391 CDP endpoints ≈ $0.53 each). The 50% price cut pre-committed in DIR-008 should be evaluated AGAINST THE MCP/task-report model ($0.05–$0.19 per task report × volume), not just a flat per-call halving — a per-call cut in a dead channel changes nothing.

## HONEST BASELINE
Revenue today and lifetime on the real rail: $0 real USDC. Nothing in this triage creates revenue; it reallocates the same shift-budget from channels with measured ceilings near zero toward the only channel with observed winners at our scale. First plausible external dollar remains weeks out, not days.

## VERIFY
```
grep -c 'channel-triage' ~/x402-agent-service/org/directives.json   # >= 1 after Planner syncs DIR-042
test -f ~/x402-agent-service/org/plans/channel-triage.md && echo PRESENT
git -C ~/x402-agent-service log --oneline -1 -- org/plans/channel-triage.md
```
Expected: file present, committed, referenced from DIR-042 entry; next Chief-of-Staff briefing cites the ranking.

## ROLLBACK
`git revert <commit>` removes the triage doc; restore DIR-042 status to `planned` in org/directives.json. No runtime systems touched — this is a planning artifact only.

## ESTIMATED REVENUE IMPACT
Indirect. Prevents continued spend (~5h/day of bot attention) on a surface capped at ~$1.17/day platform-wide and redirects it to the sole channel with observed $2K–$10K/mo individual outcomes. Does not itself move today's $0.
