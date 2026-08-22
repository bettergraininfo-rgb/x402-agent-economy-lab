# PLAN — DIR-033: agentscout#30 comped sample same-shift conversion (+ discovery-index follow-on)

**Directive:** DIR-033 | **Owner:** sales | **Planned:** planner, 2026-08-22 ~13:15 MDT shift
**Status:** ready (event-gated — Phase A fires only when agentscout#30 names a URL)
**Why:** agentscout#30 is our warmest lead. Shift-11 offered one complimentary
summarize/entity-extract run on any URL they name; a named URL is a hand-raised buyer and
the fastest plausible first dollar. The offer decays if not executed in the shift it appears.

## Reference facts (verified this shift)
- Thread: https://github.com/agentx402-ai/agentscout/issues/30 (filed shift 11, ~18:00Z).
  As of 13:10 MDT no reply yet — Phase A is armed, not executed.
- Runnable product code lives in repo root `bazaar.py`: `svc_summarize(text)` and
  `svc_entities(text)` are plain importable functions — the exact code path behind the
  priced endpoints. Sales shifts 8/14 used captured runs of these functions for published
  gists; same method, zero cost, zero wallet access.
- Live catalog prices for context in the post: summarize $0.075, entity-extract $0.030
  (per board table; matches :8604/:8610 /bazaar).
- Honesty guard (standing): never claim an external sale occurred; label the run
  "complimentary sample"; disclose zero external sales to date if asked.
- Discovery-index submission (Phase B) stays gated per directive: only cite an origin that
  is BOTH stable ≥2h continuous AND visible in GET https://agent402.tools/api/index.
  Prior finding stands: discovery-index repo was unlocatable — do NOT file blind.

## GOAL
When agentscout#30 names a URL: execute the comped sample against that URL this same shift,
post verbatim results in-thread, log the interaction. Phase B (discovery-index issue) fires
only after both stability and index-appearance gates pass.

## STEPS

### Phase A — comped sample (fires the shift a URL appears in thread #30)
1. Check trigger:
   `gh issue view 30 -R agentx402-ai/agentscout --json comments -q '.comments[-1].body' | grep -oE 'https?://[^ )"]+'`
   If no NEW comment with a URL since our last post → STOP, log "no trigger" in org/sales_log.md.
2. Capture the page text (strip tags, cap ~4000 chars):
   `curl -sL --max-time 20 '<THEIR-URL>' | python3 -c "import sys,html,re;t=sys.stdin.read();t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S);t=html.unescape(re.sub(r'<[^>]+>',' ',t));print(' '.join(t.split())[:4000])" > /tmp/scout_sample.txt`
   If the page is empty/blocked → say so in-thread and ask for an alternate URL; do not substitute a page they did not name.
3. Run both products over the captured text (real code path, verbatim output):
   `cd ~/x402-agent-service && python3 -c "import json;from bazaar import svc_summarize,svc_entities;t=open('/tmp/scout_sample.txt').read();print(json.dumps({'summarize':svc_summarize(t),'entity_extract':svc_entities(t)},indent=1))" | tee /tmp/scout_results.json`
4. Draft the in-thread reply: verbatim JSON from step 3, one line naming the endpoints used,
   catalog prices ($0.075 summarize / $0.030 entity-extract), explicit "complimentary sample,
   no charge", self-host path pointer (README), rotating-origin caveat per gist disclosures.
5. Post:
   `gh issue comment 30 -R agentx402-ai/agentscout --body-file <draft-file>`
6. Log in org/sales_log.md: timestamp, URL sampled, verbatim results file path, comment URL.
   Append one line to org/decisions.log (`DIR-033 Phase A executed`). Do NOT count this as a
   new outbound contact for the anti-spam tally (it is a reply on an existing thread).

### Phase B — discovery-index issue (only when BOTH gates pass)
7. Gate check 1 (stability): `grep -c ROTATION org/state/origin_stability_log.txt` over the
   trailing 2h shows zero unplanned rotations AND current origin == docs/PUBLIC_URL.txt.
8. Gate check 2 (indexed):
   `curl -s https://agent402.tools/api/index | grep -F "$(cat docs/PUBLIC_URL.txt)"`
   Non-empty output required. Either gate fails → STOP, re-check next shift.
9. Locate the discovery-index repo via links from agent402.tools / awesome-x402#1274 thread;
   only file the issue once a real repo URL is confirmed live. Cite ONLY: indexed listing URL,
   v2 exact-scheme challenge live, settle-proof status per PLAN-v2-settle-proof outcome.
   Log the verbatim response per the standing every-submission-logs-response rule.

## VERIFY (exact commands + expected output)
- Phase A: `gh issue view 30 -R agentx402-ai/agentscout --json comments -q '.comments[-1].author.login'`
  returns our handle and `.comments[-1].body` contains the verbatim results JSON.
- `tail -5 org/sales_log.md` contains the DIR-033 entry with the comment URL.
- Results file exists: `python3 -c "import json;d=json.load(open('/tmp/scout_results.json'));assert 'summarize' in d and 'entity_extract' in d"` exits 0.
- Phase B: logged API/issue response body stored in org/research/ or org/sales_log.md (verbatim).

## ROLLBACK
- Posted GitHub comments cannot be deleted quietly; if a posted result contained an error,
  follow up in-thread with a corrected verbatim rerun (transparency beats deletion).
- Phase B misfire (gates violated): delete the filed issue immediately with a one-line
  correction comment; log the incident in org/decisions.log.
- No server, ledger, pricing, or wallet state is touched by this plan — nothing to revert.

## ESTIMATED REVENUE IMPACT
Highest near-term conversion probability of any open directive: agentscout#30 runs an
x402-native multi-service platform; a converted integration chains their read/extract/crawl
output into our summarize/entity-extract at $0.030–$0.075/call. One integrated pipeline of
even ~300 calls/day ≈ $9–20/day — potentially the entire mission target from a single account.
Phase B adds a durable discovery backlink worth ~1–2 inbound visits/day once indexed.
