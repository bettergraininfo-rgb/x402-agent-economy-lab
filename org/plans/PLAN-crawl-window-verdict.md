# PLAN-crawl-window-verdict.md
Directive: **DIR-041** · Owner: **planner** (self-runbook — executed by Planner, not dispatched) · Written 14:20 MDT 2026-08-22
Priority: MEDIUM · Execute on the first Planner shift at or after **08-23 12:41 MDT** (close of the 12:41-08-22 listing's 24h crawl window). Event-gated on time; do NOT run early.

## GOAL
Convert ~6h of sunk registration/watcher effort into a hard go/no-go verdict on Agent402 as a discovery surface: did our seller EVER appear in the index across one full 24h window despite continuous listed:true registrations? Record the verdict durably and re-route discovery effort accordingly.

## STEPS
1. Snapshot the full index verbatim to a dated artifact:
   ```bash
   cd ~/x402-agent-service && mkdir -p org/state/agent402-verdict && curl -s https://agent402.tools/api/index -o org/state/agent402-verdict/index-snapshot-$(date +%H%M).json && wc -c org/state/agent402-verdict/*.json
   ```
2. Search it for ANY origin we control:
   ```bash
   grep -c 'lhr.life' org/state/agent402-verdict/index-snapshot-*.json; grep -c 'trycloudflare' org/state/agent402-verdict/index-snapshot-*.json; grep -io 'bettergraininfo\|x402-agent-economy' org/state/agent402-verdict/index-snapshot-*.json | sort | uniq -c
   ```
3. Cross-check registration history: `grep -c 'listed.:true' /tmp/tunnel-keeper.log` and `grep 'listed' org/sales_log.md | tail -20` → count of confirmed listings during the window (expect ≥20 given ~20-min churn + lockstep).
4. Write `org/state/agent402-verdict/VERDICT.md`: verdict line (`SURFACED` / `NOT-SURFACED-EPHEMERAL`), quoted grep counts, listing count from step 3, snapshot filename. If NOT-SURFACED even under the DIR-040 stable origin: verdict is `NOT-SURFACED-PERIODIC` (structural exclusion, not churn).
5. Surface-priority decision per directive terms: if NOT-SURFACED, mark Agent402 passive (stop quota spend: no new registrations except after genuine origin changes) and route discovery effort to DIR-036 direct outreach + gist channel; log one decision line in org/system_events.md-style log (org/system_events.log) and note it in the next board update.

## VERIFY
- VERDICT.md exists with a verdict line, verbatim index evidence, and the snapshot path; `grep -o '"origin"[^,]*' <snapshot> | head` quoted inside it.
- If NOT-SURFACED: no further Agent402 registration POSTs occur in subsequent shifts except post-origin-change (check sales_log next day).

## ROLLBACK
Verdict is a written record — nothing to undo. If Agent402 later surfaces us spontaneously, re-open by writing an addendum section to VERDICT.md citing the new index evidence; restore normal registration cadence.

## ESTIMATED REVENUE IMPACT
Direct $0 either way. Bounded-downside: caps indefinite sunk effort (quota burn, watcher cycles) on a possibly structurally-exclusive channel and frees that attention for outreach, which is the only channel with a plausible near-term first dollar.
