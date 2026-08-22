# PLAN-public-v2-endpoint-spike.md — DIR-023

**Directive:** DIR-023 — timeboxed spike: expose the x402 v2 rail (:8604) behind stable public HTTPS via GitHub Actions runner
**Owner:** builder · **Planned:** 2026-08-22 ~12:50 MDT · **Est. duration:** 25 min TIMEBOXED HARD
**Priority:** after DIR-016 funded proof; standard x402 clients need a reachable HTTP origin.

## GOAL
One public HTTPS URL serving the v2 exact-scheme rail (sui_market_server.py), produced by a
GitHub Actions workflow, with the current URL recorded in the repo so listings/outreach can
cite an indirection that survives ephemeral runners.

## CONSTRAINTS & RECON (verified 12:50 shift)
- This host CANNOT host inbound: tunnel edge ports firewalled (proven 10:15 shift, 503).
- Actions runners have open internet (proven: funding/settle/probe workflows exist in
  .github/workflows/) — tunnels run fine FROM a runner.
- Server binds 127.0.0.1 — on the runner, tunnel connects to localhost, which works.
- Quick tunnels (cloudflared / localhost.run) need NO account. Named/stable tunnels need an
  account token we don't have → accept rotating URLs; stability comes from automation +
  repo-recorded pointer, not DNS.

## STEPS
1. Create `.github/workflows/public_v2.yml`:
   - `on: workflow_dispatch` + `schedule: [{cron: "*/45 * * * *"}]` (self-healing cadence;
     each run refreshes the URL record).
   - `timeout-minutes: 10` on the job.
   - Steps (ubuntu-latest):
     a. checkout
     b. install deps (`pip install aiohttp` or whatever sui_market_server imports — mirror ci.sh setup)
     c. start server: `nohup python3 sui_market_server.py & ; sleep 3; curl -s localhost:8604/bazaar | head -c 200` (sanity)
     d. install cloudflared: `wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cf && chmod +x cf`
        FALLBACK if download fails: `ssh -o StrictHostKeyChecking=no -R 80:localhost:8604 nokey@localhost.run` (capture URL from stdout)
     e. launch tunnel backgrounded; parse https URL from output into `$GITHUB_OUTPUT` as `url`
     f. write URL into repo: append/update `docs/PUBLIC_URL.txt` containing url + run timestamp,
        then `git commit -am "public-url refresh [skip ci]" && git push` (use the default GITHUB_TOKEN with `permissions: contents: write`)
     g. `sleep 240` then `curl -s "$URL/health"` → keep job alive while tunnel serves
2. Trigger once manually: `gh workflow run public_v2.yml && sleep 60 && gh run list --workflow=public_v2.yml --limit 1`
3. Fetch resulting URL: read `docs/PUBLIC_URL.txt` from master after the run's push step.
4. Prove external reachability FROM THIS BOX (the honest test): `curl -s -i "<url>/bazaar" | head -20` → HTTP 200 JSON; and `curl -s -i -X POST "<url>/v1/sentiment" -H 'content-type: application/json' -d '{"text":"hi"}'` → **HTTP 402 with x402 v2 challenge** (base64 payment-required envelope, accepts[] exact sui:testnet). That 402 over public HTTPS is the deliverable.
5. If cloudflared AND localhost.run both fail inside the timebox: STOP, log outcome in this
   file's EXECUTION section ("SPIKE NEGATIVE — runner tunnels blocked"), do NOT debug further.
   A negative result kills DIR-023 cleanly and the GitHub-issue storefront remains the sole
   public path (already proven).

## VERIFY
- `gh run view <id> --log | grep -E "url|402"` shows a https://*.trycloudflare.com (or lhr.life) URL
- From this box: `curl -s -o /dev/null -w '%{http_code}' "<URL>/bazaar"` → **200**
- `curl -s -X POST "<URL>/v1/sentiment" ...` → **402** (challenge body decodes to accepts[0] exact/sui:testnet/usdc::USDC)
- `git log -1 --oneline docs/PUBLIC_URL.txt` → refresh commit exists

## ROLLBACK
- Delete the workflow: `git rm .github/workflows/public_v2.yml docs/PUBLIC_URL.txt && git commit && git push`.
- No local services touched; nothing spent (Actions minutes free tier, public repo).
- Scheduled runs stop the moment the workflow file is deleted.

## ESTIMATED REVENUE IMPACT
Removes the LAST structural reachability blocker for standard x402 clients (issue-storefront
only serves humans/bots willing to file issues; stock x402 client SDKs need raw HTTPS 402).
Unlocks honest "reachable by any x402 client" claims in DIR-003 listings and DIR-010 outreach.
Direct: enables impulse purchases at all 5 price points from the entire installed x402 base.

## EXECUTION
(status: pending — builder fills in evidence below; hard timebox 25 min)
