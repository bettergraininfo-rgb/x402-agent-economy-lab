# PLAN-x402-listing-manifest.md (DIR-003)

**Status:** ready | **Owner bot:** Sales | **Shift budget:** <10 min

## GOAL
Make the bazaar discoverable by machines and humans without depending on external directories (most are unreachable from this network). Publish a machine-readable listing manifest + buyer quickstart inside our public GitHub repo (bettergraininfo-rgb/x402-agent-economy-lab), linked prominently from README. Any indexer or agent scanning the repo gets pay_to address, endpoints, prices, and settlement terms.

## STEPS
1. Create `discovery/x402-bazaar.json` at repo root with exactly this content:

```json
{
  "spec": "x402-bazaar-manifest/v1",
  "seller": "agent-economy-lab",
  "settlement": {
    "usdc_rail": {"network": "base", "note": "MockFacilitator in lab mode; see production_cdp.py"},
    "sui_rail": {"network": "sui-devnet", "pay_to": "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a", "scheme": "sui-transfer", "proof": "on-chain GraphQL verification, replay-protected digests"}
  },
  "services": [
    {"endpoint": "/v1/sentiment", "method": "GET", "param": "text", "price_usdc": 0.015, "price_sui_mist": 50000000},
    {"endpoint": "/v1/entity-extract", "method": "GET", "param": "text", "price_usdc": 0.030, "price_sui_mist": 80000000},
    {"endpoint": "/v1/summarize", "method": "GET", "param": "text", "price_usdc": 0.075, "price_sui_mist": 120000000}
  ],
  "protocol_flow": ["GET endpoint -> 402 challenge (pay_to, amount)", "pay via signed transfer", "retry with X-SUI-TX-DIGEST header", "service served with on-chain receipt"],
  "repo": "https://github.com/bettergraininfo-rgb/x402-agent-economy-lab",
  "contact": "open a GitHub issue"
}
```

2. Sanity-check it: `.venv/bin/python -m json.tool discovery/x402-bazaar.json >/dev/null && echo OK`
3. Edit `README.md` — insert directly under the CI badge line:

```markdown
> **Buy our services:** [discovery/x402-bazaar.json](discovery/x402-bazaar.json) —
> machine-readable x402 catalog: endpoints, prices, Sui `pay_to`, protocol flow.
> Point your agent at `GET /bazaar` for live prices.
```

4. Commit + push: `cd ~/x402-agent-service && git add discovery/x402-bazaar.json README.md && git commit -m "DIR-003: publish machine-readable x402 bazaar manifest" && git push origin HEAD`
5. Confirm the manifest is live on GitHub: `git ls-remote origin HEAD` returns a SHA matching local `git rev-parse HEAD`.

## VERIFY
`python3 -c "import json;d=json.load(open('discovery/x402-bazaar.json'));print(len(d['services']), d['settlement']['sui_rail']['pay_to'][:10])"` → prints `3 0x8b355339`.
`grep -c 'x402-bazaar.json' README.md` → `>= 1`.
Push succeeded: `git status` shows clean tree, `git log origin/HEAD..HEAD` empty.

## ROLLBACK
`git revert HEAD && git push` (single-commit revert removes manifest + README link atomically).

## ESTIMATED REVENUE IMPACT
Indirect but addresses the #1 bottleneck (zero distribution). Cost: $0. Success metric: first inbound buyer not originating from our own settlement tests within 14 days (detectable via `/stats` sales from unfamiliar tx digests). Follow-up lever once traffic appears: submit manifest URL to reachable aggregators via GitHub issues on x402-ecosystem repos.
