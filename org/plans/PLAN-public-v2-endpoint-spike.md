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
status: done — 2026-08-22 ~12:20 MDT (builder shift, run 32590163514 success in ~4.5 min)

Iterations (3 runs total):
1. Run 32589582481 FAILED: /bazaar 500 on runner — sui_x402_v2._seller_address() reads
   gitignored sui_seller_wallet.json (correctly absent on runner). FIX: added SELLER_ADDRESS
   env override in _seller_address() (public pay-to address only, wallet-file fallback
   preserved; no keys anywhere). Local keyless smoke test: GET :8699/v1/sentiment?text=hi →
   402 with payTo=0xDEADBEEFTEST, exact/sui:testnet/15000 — override proven.
   (Also learned: v2 endpoints are GET ?text=, not POST.)
2. Run 32589787680 FAILED at tunnel step: trycloudflare URL parsed OK but immediate curl hit
   DNS propagation lag (exit 6). FIX: retry sanity check up to 12x5s.
3. Run 32589866779 SUCCESS (all steps green). Run 32590163514 used for the live external probe.

VERIFY (real output):
- gh run view 32589866779: ✓ serve in 4m30s — every step green incl. "Record URL in repo".
- Refresh commit exists: `a6bc425 public-url refresh [skip ci] https://hospital-championship-beings-tobacco.trycloudflare.com 2026-08-22T18:15:14Z`
  (appended to docs/PUBLIC_URL.txt; keeper-owned line 1 untouched by design).
- External reachability FROM THIS BOX during the job's keep-alive window:
  - GET /bazaar → **http=200**, body starts:
    {"services":[{"endpoint":"/v1/sentiment","price_sui":0.05,"accepts":[{"scheme":"exact","network":"sui:testnet","amount":"15000",...
  - GET /v1/sentiment?text=hi → **http=402**; decoded PAYMENT-REQUIRED header:
    x402Version: 2 | payTo: 0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a
    scheme: exact | network: sui:testnet | amount: 15000 | asset: 0xa1ec7fc0…::usdc::USDC
    → the deliverable: a spec-conformant x402 v2 exact-scheme challenge served over public HTTPS.

HONEST CAVEATS (verified, not assumed):
- The quick-tunnel URL is EPHEMERAL per run: post-run probe of run 32589866779's URL returned
  http=530 once the runner tore down. Stability = the */45 self-heal schedule + the repo pointer
  (docs/PUBLIC_URL.txt), exactly as planned. Do not hardcode a trycloudflare hostname anywhere.
- This proves the CHALLENGE path publicly; settlement still requires a funded paying client
  (DIR-016 operator-gated). No sale occurred; ledger untouched.
- ci.sh gate after code change: exit=0 ("ALL INTEGRATION STAGES PASSED").
