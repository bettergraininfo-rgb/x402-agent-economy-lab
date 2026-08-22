# DIR-017 — Marketplace Listing Drafts (Phase A staged 2026-08-22 ~11:30 MDT, sales shift 10)

UPDATE (same shift, post-Phase-B): Agent402 LISTED successfully. Origin moved from
`https://7c570776e5bb1d.lhr.life` to `https://bcb3c875793cc7.lhr.life` (anonymous
subdomains rotate on reconnect) — ops/tunnel-keeper.sh now maintains the tunnel AND
re-registers the current subdomain with agent402.tools/api/index/register automatically.
Outcome table at bottom of this file is authoritative.

Status legend per PLAN-listing-drafts-prestage.md v2. All prices below were sanity-checked
against the LIVE catalog (`curl http://127.0.0.1:8604/bazaar`, captured 11:26 MDT this shift)
and against the live public origin before drafting. No invented figures.

## ORIGIN FACTS (captured live this shift — not assumed)
- Public origin: `https://7c570776e5bb1d.lhr.life` — VERIFIED externally:
  `GET /bazaar` → HTTP 200; `GET /v1/sentiment?text=hello` → HTTP 402 with
  `payment-required:` base64 header decoding to
  `{"x402Version":2,"accepts":[{"scheme":"exact","network":"sui:testnet","amount":"15000",
  "asset":"…::usdc::USDC","payTo":"0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a","maxTimeoutSeconds":600}]}`.
- Backend: sui_market_server.py :8604 (dual dialect: legacy X-SUI-TX-DIGEST + x402 v2
  PAYMENT-SIGNATURE; PAYMENT-SIGNATURE present at sui_market_server.py:152). DIR-011 CLOSED.
- Live catalog (Sui rail): /v1/sentiment $0.015 · /v1/entity-extract $0.030 ·
  /v1/summarize $0.075 (testnet-USDC amounts 15000/30000/75000).
- HONESTY DISCLOSURES that must survive into any submission:
  1. Origin is an anonymous localhost.run tunnel subdomain — EPHEMERAL until ops makes it
     persistent (ops task flagged in board.md this shift). Agent402 drops unreachable
     origins from ROUTING only ("never off the roster"), so worst case is recoverable.
  2. Settlement rail is sui:testnet USDC via facilitator exact scheme; one real v2 settle
     not yet proven (DIR-020 open). Legacy devnet-SUI digest path settles real on-chain.
  3. Real-USDC Base purchases exist ONLY via the GitHub-issue storefront
     (bettergraininfo-rgb/x402-agent-economy-lab, on-chain verified, reject-path e2e proven).
  4. Zero external sales to date. Never claim otherwise.

## Section 1 — Agent402 payload [READY — SUBMITTED this shift, see sales_log]
Actual API is one field (verified from agent402.tools/sell live this shift):
```json
{"origin": "https://7c570776e5bb1d.lhr.life"}
```
Submission command:
```
curl -s -X POST https://agent402.tools/api/index/register \
  -H 'content-type: application/json' \
  -d '{"origin":"https://7c570776e5bb1d.lhr.life"}'
```
Post-submit verify: crawler probes hourly → check `https://agent402.tools/api/index`
for our origin within ~24h. Note: their buyer chains are EVM/Solana/etc — NO Sui lane —
so routing demand is expected ~zero; value is indexed presence + backlink (credibility
artifact per RQ-017 reclassification).

## Section 2 — Discovery-index issue text [BLOCKED — target repo unverified]
"x402-discovery-index" could NOT be re-located on GitHub this shift (repo search returned
no such repo under that name; findings.md reference from shift 2 may be stale/renamed).
Per plan rule "stop and log if any channel's target cannot be reached": NOT filed blind.
Prepared body (hold until a verified issue-based index repo is identified):
> Title: Machine-payable NLP micro-services (x402 v2 exact scheme, sui:testnet USDC)
> Body: sentiment $0.015 / entity-extract $0.030 / summarize $0.075 per call.
> Live 402: `curl https://<ORIGIN>/v1/sentiment?text=hello`. Sample challenge:
> {"x402Version":2,"accepts":[{"scheme":"exact","network":"sui:testnet","amount":"15000","asset":"…::usdc::USDC"}]}.
> Real-USDC alternative purchase path: GitHub-issue storefront w/ on-chain verification
> (repo above). Self-host: one command from repo. Honest status: no external sale yet;
> tunnel origin ephemeral pending persistent hosting.

## Section 3 — PayAPI Market answers [BLOCKED — human-gated + rail mismatch]
Listing wizard (payapi.market/list, verified live this shift) requires: name, EMAIL,
Base USDC payout wallet, base URL, then THEIR verification buy over Base-mainnet x402.
Two gates: (a) email/wizard = human step like Render signup; (b) our public origin speaks
sui:testnet, not Base x402 — submitting now would fail their settlement verification.
Answers pre-drafted for when the Base rail gets a public origin (or Rail402 gateway mode):
- What it does: Sentiment analysis, entity extraction, text summarization as pay-per-call JSON APIs.
- Auth model: x402 payment-required (HTTP 402 → on-chain USDC → retry); no keys/accounts.
- Pricing: $0.015/$0.030/$0.075 per request (premium report/batch SKUs via storefront).
- Contact: https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/issues

## Submit checklist outcome (Phase B, this shift)
| Channel | Outcome |
|---|---|
| Agent402 | SUBMITTED — see sales_log shift-10 line for response |
| discovery-index | BLOCKED (target repo unverified) |
| PayAPI | BLOCKED (email wizard + Base-rail mismatch) |
