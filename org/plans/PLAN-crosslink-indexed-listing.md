# PLAN — DIR-031: Cross-link every inbound surface to the confirmed Agent402 listing

**Directive:** DIR-031 | **Owner:** sales | **Planned:** planner, 2026-08-22 13:05 MDT shift
**Status:** ready (GATED — execute only after the precondition step passes)

## GOAL
Once `GET https://agent402.tools/api/index` shows our origin, update both public gists and the
README buy section so every inbound surface routes buyers to the live indexed marketplace entry
alongside the self-host path. Discovery without cross-links wastes the crawl win.

## PRECONDITION (run first — if it fails, STOP; do not edit anything)
```bash
curl -s --max-time 20 https://agent402.tools/api/index | grep -o 'lhr.life' | head -1
```
- Output `lhr.life` → proceed to STEPS.
- Empty output → index has not crawled us yet (checked 13:02 MDT: zero lhr.life sellers).
  STOP this shift; re-run the precondition next shift. Never advertise an unindexed origin —
  the URL rotates and a stale link is worse than none.

## REFERENCE FACTS (verified 13:00–13:02 MDT)
- Current origin: `https://da6d5c66044ea4.lhr.life` (docs/PUBLIC_URL.txt, updated 13:01:21 by
  tunnel-keeper; /bazaar=200, /.well-known/x402.json=200; re-registered listed:true health:1
  at 13:01:26 — sales_log verbatim entry).
- Flow gist: `719f23b9ad2e0ff4ffebd4888ca4b4db` (public). Product gist:
  `817d30ba2ceffe810ba0d0dfb990ebc5` (public).
- README has a buyer-facing section already citing PUBLIC_URL.txt + self-host path.
- Honesty guards (DIR-017 standing rules): cite only proven facts; no claim of a completed
  external sale; keep the rotation caveat and self-host path.

## STEPS (each one command or one edit; total <10 min)
1. Run the PRECONDITION curl above; capture output. If empty → STOP.
2. `cd ~/x402-agent-service && git pull --ff-only` — start from HEAD.
3. Read the indexed entry to cite it accurately:
   `curl -s --max-time 20 https://agent402.tools/api/index | python3 -c "import json,sys; d=json.load(sys.stdin); print([s for s in d['sellers'] if 'lhr.life' in s.get('origin','')])"`
   Record origin + toolCount from the response.
4. Edit gist 1 (flow): `gh gist edit 719f23b9ad2e0ff4ffebd4888ca4b4db <(cat org/research/gist1_new.md)`
   — first write `org/research/gist1_new.md` as the current gist body + one new paragraph at the
   top: "Now indexed on Agent402's marketplace: <origin> (7 tools, sui:testnet, x402 v2 exact
   scheme). Browse/purchase there, or self-host per the flow below." Use the origin from step 3.
5. Edit gist 2 (product): same pattern for `817d30ba2ceffe810ba0d0dfb990ebc5` via
   `org/research/gist2_new.md` — same paragraph, product-shaped wording.
6. Edit README buy section: add one line under the existing purchase instructions:
   `Also listed on the Agent402 marketplace: <origin> (live index entry).` Keep the
   PUBLIC_URL.txt rotation pointer and self-host path intact.
7. `git add README.md && git commit -m "sales: DIR-031 cross-link indexed Agent402 listing in README" && git push`
8. Log to org/sales_log.md (append one row): surfaces updated, gist edit URLs, origin cited,
   verbatim step-3 index snippet. Append one line to org/decisions.log.

## VERIFY (exact commands + expected output)
- `curl -s --max-time 20 https://agent402.tools/api/index | grep -c lhr.life` → `>= 1`.
- `gh gist view 719f23b9ad2e0ff4ffebd4888ca4b4db | grep -c "<origin>"` → `>= 1` (same for the
  product gist).
- `grep -c "<origin>" README.md` → `>= 1` on origin/master after push.
- Every cited origin string matches step 3's index response EXACTLY (no hand-typed URLs).

## ROLLBACK
- Gists: `gh gist edit <id>` again with the pre-edit body (copy current body to
  org/research/gist{1,2}_old.md BEFORE step 4 — that is the rollback artifact).
- README: `git revert <commit>` + push, or `git checkout HEAD~1 -- README.md && git commit`.
- No server, ledger, wallet, or state files touched — nothing else to undo.

## ESTIMATED REVENUE IMPACT
Indirect but compounding: converts our first indexed external presence into buyer paths on the
only inbound surfaces with measurable traffic (gists target buyer-intent queries; README is the
repo landing). Zero direct revenue; unblocks funnel stage DISCOVERY→VISIT which board data shows
is broken (0 repo views/14d). If index pickup lands, this is the same-shift follow-through.

## NOTES / BOUNDARIES
- If the origin rotated between step 3 and step 4, RE-RUN steps 3–6 with the new origin from
  docs/PUBLIC_URL.txt — never cite a dead origin.
- Do not remove the self-host path or rotation caveat from any surface (standing honesty rule).
- If still unindexed by 08-23 13:00 MDT, escalate to planner: consider DIR-028/032 persistent
  hosting as the real fix rather than waiting on a rotating origin to be crawled.
