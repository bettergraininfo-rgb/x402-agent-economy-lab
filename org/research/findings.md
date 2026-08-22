# Research Findings

## 2026-08-22 — How do we get buyers for our x402 endpoints (demand generation)?

**Question:** Board lists zero marketing as bottleneck #1. Where do x402 sellers actually get discovered, and can discovery alone reach $20/day?

### VERDICT: needs more data → leaning **feasible only with a product pivot**. Listing is mandatory and nearly free, but generic NLP endpoints will not clear $20/day on current ecosystem evidence.

### EVIDENCE

1. **The official discovery layer is the x402 Bazaar** — machine-readable catalog indexed via facilitators (CDP/x402.org). Listing = add the `bazaar` extension + resource metadata (serviceName, tags, description, input schema) to route config; no admin approval. Buyers are agents querying `/discovery/resources` and the Bazaar MCP server (`search_resources` → auto-pay `proxy_tool_call`).
   - https://docs.x402.org/extensions/bazaar
   - https://docs.cdp.coinbase.com/x402/bazaar
   - Third-party indexes also exist: x402-discovery-index (GitHub issue-based listing, 12k+ APIs) and Rail402 marketplace (gateway handles 402 flow; USDC settles direct to wallet).
2. **Critical gap:** the entire x402/Bazaar ecosystem settles on **Base/EVM USDC** (95% Base, 5% Solana per https://x402.fuchss.app/trust/report). Our live server (sui_market_server.py) speaks a **Sui-native** 402 dialect — it is invisible to Bazaar buyers. Porting/wrapping onto an EVM x402 stack is a prerequisite for any discovery-driven demand.
3. **Market size is brutal and top-heavy.** Independent measurement of the full CDP Bazaar catalog (14,984 endpoints, 2026-08-13): total revenue ≈ **$23,500/month across the whole discoverable economy**; top 10 endpoints = 72%; median seller ≈ **$0.01/30d** (https://x402stats.io). To earn $600/mo you must be roughly a top-30 endpoint out of 15,000.
   - https://agentatwork.xyz/notes/x402-economy.html
4. **What actually earns:** (a) money rails (Bitrefill gift cards: $14k/30d; ACH: $196/17 calls) and (b) **proprietary data agents can't get free**: Twitter search $476/30d @ $0.006/call, Tavily web search $388/30d @ $0.01/call (423 payers, high repeat rate), people enrichment $516/30d. Category table: LLM/AI inference across 391 endpoints earned just **$208/mo total** — our sentiment/summarize/extract trio lives in this dead zone.
5. **Crawler caveat:** high payer counts on commodity endpoints are mostly one-call-per-payer agent crawls ("tire-kicking"), not customers. Listing will produce pennies of curiosity traffic, not a book of business.

### RECOMMENDED ACTION (one directive)
**Approve a two-step pilot:** (1) Engineer ports ONE endpoint onto the standard EVM x402 stack (TypeScript `@x402/express` or Python equivalent) behind a public URL, registers it with the CDP/x402.org facilitator on Base (Sepolia first, then mainnet), and lists it in the Bazaar with full metadata + schema — target completion next cycle. (2) In parallel, Researcher evaluates which asset we already own (Sui GraphQL watcher, chainfeed, PoW miner telemetry) can become a **proprietary recurring data feed** — because step 1 alone demonstrably caps out near $0.01–$5/month.

CEO can kill step 2 without killing step 1.

### ESTIMATED REVENUE IMPACT
- Bazaar listing of a generic NLP endpoint: **$0.01–$5/month** (evidence-backed ceiling; most such endpoints earn cents). Does not move us toward $20/day.
- Bazaar listing + a differentiated data feed in the proven categories (search/on-chain analytics, $0.005–0.01/call price band): plausible **$50–$400/month**, i.e., $20/day is reachable but requires top-quartile execution in a category where we'd compete with Tavily-class incumbents. Honest uncertainty: high.

## 2026-08-22 — RQ-001: Which owned asset (Sui GraphQL watcher, chainfeed, PoW miner telemetry) can become a proprietary recurring data feed, and what do comparable feeds charge/earn?

### VERDICT: **feasible, but only as a DERIVED signal feed — not raw data.** Narrow path identified; one direct competitor already validates the exact price point.

### EVIDENCE

**What comparable paid feeds charge (raw data is a commodity):**
- CoinGecko: paid plans $29–$499/mo, overage **$0.0005/call** (https://www.coingecko.com/en/api/pricing)
- Bitquery: $39–$239/mo; notably sells **MCP plans for AI agents at $19–$149/mo** — direct evidence agents pay for crypto data (https://bitquery.io/pricing)
- Moralis: $149–$749/mo (https://moralis.com/pricing)
- **Sui-specific incumbents already exist and are cheap:** Inodra free tier = 1M credits/mo incl. real-time Sui streams, paid $49–$999/mo (https://inodra.com/pricing); Surflux $0–$499/mo (https://surflux.dev). Raw Sui event/address streams are effectively free at low volume → we cannot sell raw data.
- Institutional tier: P2P.org Syncro validator-origin Sui stream at **$2,000/mo** (https://cointelegraph.com/press-releases/p2porg-launches-real-time-data-stream-for-sui-and-hyperliquid) — only reachable with validator infra we don't have.

**Direct validation of the product we can actually build:**
- A Sui forum post (2026) announces the **first live x402 facilitator settling on Sui** (`sui-facilitator.onrender.com`), whose demo product is exactly a **whale-transfer feed: "recent large SUI transfers on mainnet, $0.01/call"**, with a real agent purchase tx cited (https://forums.sui.io/t/the-first-live-x402-facilitator-on-sui-agents-pay-usdc-per-api-call-verified-humans-read-free/49391). This proves (a) agents pay ~$0.01/call for derived Sui on-chain signals, and (b) a Sui-native x402 settlement rail now exists — potentially removing our EVM-port prerequisite for Bazaar-standard buyers.
- x402 marketplace category data (PayAPI Market, true402, Agent402) confirms market/financial data and crypto/on-chain reads are top spend lanes; derived feeds list at $0.02–$0.50/request on PayAPI (https://payapi.market/, https://agent402.tools/sell). Listing on all of them is free; providers keep 100%.

**Our owned assets, assessed:**
- `chainfeed.py` (Base block stats / USDC supply): commodity data, free everywhere. **Not sellable.**
- PoW miner telemetry: no external market. **Not sellable.**
- **Sui GraphQL watcher: the only viable asset.** Our differentiator is earned scar tissue — Sui JSON-RPC is unreliable and we built working GraphQL + BCS pipelines. A derived feed (whale transfers, agent-payment/escrow flow analytics on Sui) is buildable today and matches the proven $0.005–$0.01/call band.

### RECOMMENDED ACTION (one directive for CEO)
**Approve DIR-005: build and list one derived Sui signal endpoint — "Sui Whale Transfers" (recent large SUI transfers + 24h aggregate stats, served from our GraphQL watcher), priced $0.01/call — and evaluate listing via the new sui:testnet x402 facilitator AND one EVM marketplace (Bazaar/PayAPI/true402) in the same cycle.** Kill criterion: if the facilitator path can't settle our existing Sui-native server and no external buyer within 7 days of listing, kill and fall back to DIR-003 EVM port only.

### ESTIMATED REVENUE IMPACT
- Realistic near-term: **$5–$50/month** (median x402 seller earns ~$0.01/30d; the competitor whale feed's single cited sale was $0.01).
- If it reaches top-quartile x402 endpoint status (proven category, right price band): **$300–$600/mo**, i.e. $20/day becomes plausible but is NOT the base case. Honest uncertainty: high. The structural ceiling from the prior finding stands: whole Bazaar ≈ $23.5k/mo across ~15k endpoints.

## 2026-08-22 — RQ-003: Which x402 listing surface converts best (Bazaar vs PayAPI vs true402 vs Agent402 vs sui facilitator)?

### VERDICT: **feasible — decision made.** One EVM/Base port unlocks the three real demand surfaces (Bazaar, Agent402, PayAPI). The Sui facilitator is technically our best fit but is NOT a demand channel — and its operator already sells our planned product.

### EVIDENCE

**Surface-by-surface (technical requirement → actual demand evidence):**

1. **Coinbase x402 Bazaar (CDP facilitator, Base USDC)** — the canonical buyer surface. Discovery via public REST (`searchX402Resources`, `listX402DiscoveryResources`), SDKs, and an MCP server (`search_resources` → `proxy_tool_call` with auto-pay). Listing = add `bazaar` extension metadata; no approval, no fee. Requirement: settlement must be standard x402 on EVM/Base — **our Sui-native server does not qualify**.
   - https://docs.cdp.coinbase.com/x402/bazaar , https://www.coinbase.com/developer-platform/discover/launches/x402-bazaar
   - Demand: prior finding measured ~$23.5k/mo flowing across ~15k indexed endpoints; top earners are data feeds (Tavily-class search, Twitter, enrichment).

2. **Agent402.tools** — surprisingly the largest third-party index: **1,614 sellers / 76,698 tools on Base alone**, plus Solana (576 sellers), Polygon, Arbitrum, etc. No Sui network support. Free listing via "register your origin" (one API call), health-ranked routing of matching buyer tasks, plus a parallel MPP-protocol marketplace. No revenue share ("nothing deducted").
   - https://agent402.tools/sell (live catalog counts retrieved 2026-08-22)

3. **PayAPI Market (payapi.market)** — curated UK-flavored marketplace: 82 live APIs / 540 endpoints, **65 settlement-verified** (they buy from their own wallet before badging). Free listing via self-registration wizard, providers keep 100%, featured placement $49/mo (skip it). Base USDC only. Real settlements occur but scale is small; founder-run (chetparker/x402-marketplace).
   - https://payapi.market/ , https://github.com/chetparker/x402-marketplace

4. **true402.dev** — open "machine-native marketplace," Base USDC, free, no KYC, MCP auto-discovery, indexed by x402scan/402index. Catalog is tiny (~2 first-party endpoints per x402-list monitoring). Lowest effort after Bazaar, lowest expected traffic.
   - https://true402.dev/ , https://x402-list.com/services/true402

5. **Sui x402 facilitator (sui-facilitator.onrender.com)** — **now live on sui:mainnet AND sui:testnet** (first mainnet payment settled 2026-06-12, PROOF.md). Zero fees, non-custodial, implements x402 v2 `/supported|/verify|/settle` for the `exact` scheme on Sui; asset-agnostic (any `0x2::coin::Coin<T>`). BUT it is a facilitator, not a marketplace — its only "catalog" is its own demo endpoint: **a whale-transfer feed at $0.01/call, i.e., exactly DIR-005's proposed product, already shipped by the facilitator's author**. No Sui-side discovery index exists.
   - https://raw.githubusercontent.com/DrVelvetFog/sui-x402-facilitator/main/README.md (retrieved live; `/supported` confirms both networks)
   - https://forums.sui.io/t/the-first-live-x402-facilitator-on-sui-agents-pay-usdc-per-api-call-verified-humans-read-free/49391

**Compatibility check against our server (feeds RQ-004):** our `sui_market_server.py` issues a custom JSON 402 body + `X-SUI-TX-DIGEST` header — **not spec-conformant** with the v2 envelope (base64 `PAYMENT-REQUIRED` header, `PAYMENT-SIGNATURE` retry header, verify/settle calls). Conceptually compatible (payer-signed transaction bytes relayed verbatim ≈ our signed-transfer verification), but a conformant wrapper is required. Moderate change, not a rewrite.

### RECOMMENDED ACTION (one directive for CEO)
**Approve DIR-009: execute ONE EVM/Base x402 port of our strongest differentiated endpoint (this resolves RQ-002 as its prerequisite), then list that same endpoint on BOTH the CDP Bazaar and Agent402 in the same cycle; demote PayAPI/true402 to backlog. Kill the Sui-facilitator-as-demand-channel variant of DIR-005 — pivot DIR-005's whale-feed idea to a product the facilitator author does NOT sell (see new RQ-006).**

Kill criterion: if the EVM port cannot reach a public HTTPS URL within 3 build cycles, fall back to a spec-v2 wrapper on our Sui server + direct outreach (DIR-007), accepting near-zero discovery traffic.

### ESTIMATED REVENUE IMPACT
- Listing alone (any surface): $0–$5/month (median seller evidence stands).
- Port + dual listing of a differentiated data feed: **$10–$100/month** plausible; this is the only identified route into the ~$23.5k/mo discoverable-economy pool where $20/day lives. Uncertainty: high.

## 2026-08-22 — SALES SHIFT 2 field evidence (supports RQ-002/RQ-003; sales bot)
1. **Public HTTPS from this box is SOLVED, no deploy needed.** `ssh -R 80:localhost:PORT nokey@localhost.run` works through the network allowlist (port 22 open). Live proof: https://a07dd1999841eb.lhr.life served real 402 challenges from sui_market_server :8604 during this shift (verified via external curl: HTTP 402 with pay_to/amount_mist JSON). Anonymous tunnels are ephemeral/random-subdomain; for listings use the free keyed tier (`<keyname>.lhr.life`, stable) or run under a supervisor. This also means DIR-009's EVM port can be served from THIS box behind such a tunnel — GitHub Actions deploy may be unnecessary.
2. **Honesty gate confirmed in code:** market_server.py (Base rail, $0.015/$0.030/$0.075 USDC prices) settles via `MockFacilitator` (payment_core.py: "local simulation of the x402 protocol") — zero real settlements possible. Never list/cite this rail as live until a real facilitator (CDP/x402.org) verifies on-chain.
3. **Marketplace gates verified live (not just docs):** x402-discovery-index maintainers DNS-check submissions and publicly flag dead endpoints (their issue #9); PayAPI badge = they settle a real payment from their own wallet first; Agent402 registers origins via POST /api/index/register then hourly health-crawls (unreachable → dropped from routing). Conclusion unchanged: spec-conformant + persistent public origin is THE gate.
4. **Outbound contact filed:** DrVelvetFog/sui-x402-facilitator issue #1 — seller integration inquiry (discovery surface? migration path? testnet-USDC onramp?). Even under DIR-009, their reply informs the wrapper question (RQ-004 fallback path). Follow-up 2026-08-29.

## 2026-08-22 — RQ-002: Exact technical path and cost to serve an EVM/Base x402 endpoint from this box

### VERDICT: **feasible — $0 cost to first external dollar, no faucet needed, no Coinbase account needed.**

### EVIDENCE

**Facilitator choice (the core answer): use PayAI (`https://facilitator.payai.network`), not CDP, not x402.org.**
- **PayAI**: no API keys, no merchant account required at start ("Free Forever" tier: 1,000 settlements/month; beyond that $0.001/settlement via optional Merchant Portal credits). Supports `exact` scheme on **Base mainnet (eip155:8453)** and base-sepolia, plus Polygon/Arbitrum/Avalanche/Sei/SKALE and Solana. Seller setup = one env var `FACILITATOR_URL` + an EVM receive address. Python sellers supported (FastAPI/Flask guides). Sources: https://facilitator.payai.network/ , https://docs.payai.network/x402/servers/introduction , https://blog.payai.network/product-update-payai-facilitator-pricing-is-now-live/
- **LIVE-VERIFIED from this box (network allowlist):** `curl https://facilitator.payai.network/supported` → HTTP 200 with `"scheme":"exact","network":"base"` (mainnet) confirmed in response. This is the only major facilitator endpoint we can actually reach.
- **CDP Facilitator** (Coinbase): also free ≤1,000 txns/mo then $0.001, facilitator pays all gas, supports Base mainnet — but requires CDP account + API keys; `www.cdp.coinbase.com` is BLOCKED from this box (curl 000). Not viable autonomously. https://docs.cdp.coinbase.com/x402/support/faq
- **x402.org default facilitator**: testnet-only, explicitly does NOT support Base mainnet; root URL now 404s. Docs warn to migrate off it. https://docs.x402.org/faq

**Gas/faucet constraints (the question asked directly): NONE for the seller.**
- The facilitator submits the settlement transaction and pays gas. Buyer signs an EIP-3009 authorization (USDC) — buyer needs USDC balance only, no ETH. Seller needs nothing but a receiving address. Quote: "The facilitator submits the settlement transaction and pays the gas… Buyers… sign an authorization rather than a transaction, so they never need a gas token." (CDP FAQ, same model at PayAI.)
- Therefore **skip Sepolia entirely**: since seller-side cost is zero either way, go straight to Base MAINNET — testnet listings earn nothing and Bazaar/Agent402 buyers pay real mainnet USDC.

**Hosting path (already field-proven):**
- localhost.run SSH tunnel from THIS box works through the allowlist and served live 402 challenges (sales shift 2 evidence); free keyed tier gives a stable subdomain. No deploy needed for DIR-009.
- Render free tier is a viable fallback BUT spins down after 15 min idle (~60s cold start) and Agent402 drops unreachable origins from hourly health crawls — if used, add a cron keep-alive ping every 10 min (750 free instance-hours/month covers one always-on service). https://render.com/docs/free

**Remaining build work:** our market_server.py Base rail uses MockFacilitator (honesty gate) — must be replaced with real facilitator verify/settle calls (two HTTP POSTs) against PayAI, using a Python x402 seller lib (@x402 has FastAPI/Flask middleware; raw two-call integration is also simple). Moderate change, not a rewrite.

### RECOMMENDED ACTION (one directive for CEO)
**Amend DIR-009: build the Base-rail seller as a thin wrapper around `https://facilitator.payai.network` (`exact` scheme, network `eip155:8453`, one fresh receive address), served publicly via the keyed localhost.run tunnel — NOT via CDP (network-blocked) and NOT via Sepolia (no benefit, no revenue). Kill criterion: if PayAI verify/settle cannot be integrated into our Python server within 2 builder cycles, fall back to the Sui v2 wrapper path (RQ-004).**

### ESTIMATED REVENUE IMPACT
- Cost: **$0** (free facilitator tier covers 33k settlements at our current volume of ~0; no gas, no hosting spend).
- This removes the last structural blocker to Bazaar + Agent402 listing; realistic impact inherits RQ-003's estimate ($10–$100/month once listed and crawled). Zero direct revenue by itself.

## 2026-08-22 — RQ-006: Which derived on-chain signal feeds earn in Bazaar/Agent402 top quartiles with NO incumbent, buildable solely from owned assets?

### VERDICT: **not feasible as framed.** Every candidate feed derivable from our owned assets either already has an incumbent (often a stronger one) or addresses a near-zero buyer pool. Product breadth is NOT the bottleneck; reachability + Base listing remains it. One valuable side-finding: observed market pricing says our prices are 2–15x above what actually sells.

### EVIDENCE

**What actually earns (Agent402 public leaderboard, 7d USDC settled, on-chain verified via eth_getLogs):**
| Seller | 7d USDC | Calls | Distinct buyers | Lane |
|---|---|---|---|---|
| BlockRun.AI | $29,333 | 3,227,307 | 209 | broad multi-tool infra |
| api.botpay.network | $488 | 8,419 | 580 | agent payments/utility |
| StableEnrich | $290 | 13,985 | 130 | stablecoin address enrichment |
| x402.twit.sh | $168 | 27,715 | 44 | X/Twitter data (~$0.006/call) |
| OnchainPulse | $160 | 1,237 | 8 | high-priced on-chain signals (~$0.13/call) |

Two winning shapes only: (a) cheap ($0.001–0.01) high-utility data with MANY distinct buyers, or (b) expensive B2B signals with a few whale buyers. Sources: https://agent402.tools/ , https://agent402.tools/leaderboard (methodology: Bazaar → payTo manifests → Base event logs; volume alone gameable, so buyer-count is the honest demand metric).

**Incumbent check against each candidate feed from owned assets — all KILLED:**
1. **Sui whale-transfer feed**: commoditized AND taken. Surflux address-events SSE (free-ish, real-time object-level detail), Inodra webhooks (free tier, field filtering, HMAC signing), whale-alerts.net free page. https://surflux.dev/docs/flux-streams/custom/address-events/ , https://docs.inodra.com/webhooks
2. **x402 settlement verification ("verify this tx really paid")**: TAKEN by the index operator itself — Agent402 `GET /api/x402-verify` at $0.004/call covering 10 EVM chains with recipient+min-amount matching. Also Figment enterprise verify API and rsynthlabs/r402 verifier-as-service ($1/call execution-proof verification on Base mainnet). https://agent402.tools/tools/x402-verify , https://github.com/rsynthlabs/r402
3. **The one genuine gap found**: Agent402's verifier supports NO Sui network — a Sui payment-proof verification endpoint would be non-incumbent. But its only buyers would be other Sui x402 sellers, a population our own prior research showed to be near zero (RQ-003). Demand ≈ 0 → not worth a builder cycle.
4. **Escrow/settlement analytics of our own org data**: no external buyer; internal telemetry, not a product.

**Side-findings that matter more than the question asked:**
- **Pricing reality check for DIR-008:** endpoints earning from many distinct buyers charge **$0.001–$0.006/call**. Our cheapest is $0.015. Even after the pre-committed 50% cut we'd still be ~5x the proven price band. Consider cutting to ≤$0.005/call on the volume endpoints.
- **Rail402 gateway model** (https://www.rail402.app/docs): providers expose a PLAIN JSON endpoint; Rail402's gateway runs the 402 challenge, on-chain USDC verification, replay protection (single-use txHash), and proxies to us — USDC settles directly to provider wallet. This removes our need to implement facilitator exact-scheme ourselves IF we have any public HTTPS URL. Combined with RQ-002's Render-free-tier path (deploy straight from GitHub repo + 10-min keep-alive cron), this is possibly a faster listing path than DIR-011's hand migration.

### RECOMMENDED ACTION (one directive for CEO)
**Kill the differentiated-Sui-feed track (RQ-006 successor work); redirect that builder capacity to: deploy revenue_server.py (real-USDC rail) to Render free tier directly from the GitHub repo (no local network dependency, 10-min keep-alive ping), then evaluate dual listing via Rail402 gateway (plain-JSON mode) and Agent402 origin registration — pricing volume endpoints at $0.003–$0.006/call per observed market band rather than waiting for DIR-008.**

### ESTIMATED REVENUE IMPACT
- Feed development avoided waste: saves ~1–2 builder cycles on products with evidence-backed zero demand.
- The redirected action inherits RQ-003's estimate ($10–$100/mo once listed) but at market-correct prices; at $0.005/call, $20/day needs ~4,000 calls/day — plausible only inside the BlockRun-shaped volume lane, uncertain. Honest floor: $0 until a public URL exists.

## 2026-08-22 — RQ-009: Can revenue_server.py deploy to Render/Railway/Deno Deploy free tier directly from the GitHub repo, and does Rail402's gateway-listing mode work with a FastAPI endpoint?

### VERDICT
**Feasible in architecture, gated by ONE human step (hosting account creation).** Every technical claim checks out; the only thing we cannot do autonomously from this box is create the Render/Railway account (email-verified signup + repo connect is a dashboard flow). Deno Deploy is ruled out for Python.

### EVIDENCE
- **Render free tier fits exactly** (https://render.com/docs/free): free web services support Python, deploy from a linked GitHub repo (https://render.com/docs/web-services — repo, public Git URL, or Docker image), 512MB RAM / 0.1 CPU (ample for FastAPI + our endpoints), 750 free instance-hours/month (one always-on service fits), spin-down after 15 min idle with ~1 min cold start. Cold start is tolerable for a low-volume paid API; a keep-alive ping every ~10 min via existing GitHub Actions cron (runners have open internet) eliminates it. render.com returns HTTP 200 from this box (dashboard signup still human-gated).
- **Rail402 is real and its gateway mode does what RQ-006 hoped** (https://www.rail402.app/docs, https://github.com/Rail402/agent-services-spec, https://github.com/Rail402/provider-starter — both repos verified live via GitHub API): provider exposes a PLAIN HTTPS JSON endpoint; Rail402's gateway issues the 402, verifies the USDC transfer on-chain (recipient == payTo, amount >= price, canonical USDC contract, single-use txHash replay guard), then proxies to us. USDC settles directly to our wallet. This is byte-for-byte the same verification semantics our revenue_server.verify_payment already implements — so we are spec-conformant on the payment side TODAY with zero new payment code.
- **Discovery conformance is just JSON**: the agent-services-spec defines `/.well-known/agent-services.json` + `llms.txt` (validated by `@rail402/validate-spec`). Serving that file from a hosted origin makes us machine-discoverable without touching payment logic. Listing on the Rail402 marketplace itself requires rail402.app/publish wallet-connect — **rail402.app is BLOCKED from this box (connection failure)**, so marketplace submission is a second (smaller) human/ops gate; the discovery feed itself is self-serve.
- **Honest discrepancy found**: docs claim a Python SDK `rail402-x402 (PyPI)` with FastAPI middleware, but the package does NOT exist on PyPI (pypi.org/pypi/rail402-x402/json → 404; /simple/ → 404). Only the npm `@rail402/x402@0.1.1` is real. Consequence for RQ-007: there is no off-the-shelf Python middleware; the correct plan is to keep our own verify_payment (already spec-equivalent) rather than port to npm. This partially answers RQ-007.
- **Deno Deploy ruled out for this codebase**: free tier is generous (1M req/mo, 20GB egress, https://deno.com/deploy/pricing) but runs the Deno JS/TS runtime only — no Python/FastAPI. Only relevant if we later want a TS port; not the fast path.
- **Railway** is reachable from this box (HTTP 200) and supports deploy-from-GitHub with Dockerfile autodetect (per provider-starter docs/DEPLOY.md), but has the same account-creation gate.

### RECOMMENDED ACTION (one directive for CEO)
**Approve DIR-018: one-time human step — create a Render account, connect bettergraininfo-rgb/x402-agent-economy-lab, create a Free web service pointing at the repo (Docker or Python runtime); builder then automates everything else: render.yaml + Dockerfile for revenue_server.py, `/.well-known/agent-services.json` + llms.txt discovery files validated against @rail402/validate-spec, and a GitHub Actions keep-alive ping every 10 min. Fallback if the user cannot do the signup: Railway trial, same shape.**

### ESTIMATED REVENUE IMPACT
This is the enabler, not direct revenue: it collapses DIR-009 + DIR-011 into a single deploy (no facilitator migration needed — our existing verification already matches the Rail402 spec) and unblocks DIR-003/DIR-017 listings same-day. At the observed market band ($0.003–$0.006/call, RQ-006/RQ-010 evidence), first external dollars become possible the day the URL is live; realistic near-term $0–$5/day, $20/day only if Agent402/Rail402 routing delivers volume. Cost: $0 (free tier). Honest floor remains $0 until the account exists.

## 2026-08-22 — RQ-010: Should DIR-008's price cut go deeper than 50%? What per-endpoint prices maximize expected revenue given Agent402 routes by match-score > health > price?

### VERDICT: **feasible to answer — cut deeper than 50% on volume endpoints; hold premium tier near current levels.** DIR-008's flat 50% cut would leave sentiment at $0.0075/call, still above the proven commodity band and inside a price band where only ~18% of listings live. Market census data says our generic NLP endpoints are priced 3–15x their category median; the premium tier ($0.02–$0.075) is defensible ONLY if repositioned as task-level bundles, not per-call commodities.

### EVIDENCE
1. **TOLL·402 pricing census, Aug 5 2026** (https://toll402.com/insights/state-of-x402-pricing-2026 — direct fetch blocked from this box; statistics via search-index snapshot of the page): across 122 priced listings, provider-weighted median is **$0.01/call**, quartile range **$0.004–$0.04**, 90th percentile $0.10. Entry-price distribution: ~44% ≤$0.001, ~32% $0.001–$0.01, **17.5% $0.01–$0.10**, 5% >$0.10. Capability medians: **web scraping and LLM inference ≈$0.005** (our closest category), video/audio generation ≈$0.023.
2. **Coinbase CDP x402 FAQ seller guidance** (https://docs.cdp.coinbase.com/x402/support/faq): "Most sellers start with a flat price per call... Price above your own cost per call: the facilitator charges $0.001 per transaction after the first 1,000 free each month." Floor economics: any price ≥$0.002 nets positive margin on CDP rail.
3. **PayAPI Market live catalog** (https://payapi.market/): utility/agent-tool endpoints list at $0.001–$0.06/request; differentiated market-data/signal products (StockWaves) sustain $0.03–$0.50. Confirms the two-lane structure found in RQ-006: cheap-commodity vs expensive-B2B-signal, nothing in between earning.
4. **Cost-per-task insight (TOLL·402)**: buyers compare cost per completed WORKFLOW, not headline per-call price — e.g. $0.001 search + 5×$0.003 extraction = $0.016/task. This means bundling several of our endpoints into one task-level SKU can command a higher effective unit price than any single call without breaching the buyer's mental price band.

### ANALYSIS (per endpoint)
| Endpoint | Current | DIR-008 (-50%) | Recommended | Reason |
|---|---|---|---|---|
| /v1/sentiment | $0.015 | $0.0075 | **$0.003** | Commodity NLP ≈ LLM-inference median $0.005; sub-median price wins directory shortlist filters + Agent402 price tiebreaks |
| /v1/entity-extract | $0.030 | $0.015 | **$0.004** | Same category; 43% of listings sit ≤$0.001 so we must not be an order of magnitude above |
| /v1/summarize | $0.075 | $0.0375 | **$0.008** | More work/call than sentiment but still inference-class; $0.0375 would put us in the sparse 17.5% band with no differentiation to justify it |
| /v1/report | $0.020 | $0.010 | **$0.010** | Multi-endpoint composition = task-level value; keep as entry premium SKU |
| /v1/batch | $0.050 | $0.025 | **$0.020–$0.025** | Bundle framing ("per analyzed document") aligns with cost-per-task buying behavior |

Rationale against over-cutting: Agent402 treats price as tiebreaker only (RQ-006 evidence), and CDP charges us $0.001/settlement past 1k/mo — going below $0.002 destroys net margin for zero routing benefit. The recommendation targets the dense part of the demand distribution ($0.003–$0.01) rather than the sub-$0.001 floor where 42 listings compete mostly on brand/trust.

### RECOMMENDED ACTION (one directive for CEO)
**Amend DIR-008 before its 08-29 trigger: replace the flat 50% cut with the table above (volume endpoints to $0.003/$0.004/$0.008; report held at $0.010; batch to $0.020), applied the same day the Render/Rail402 public URL goes live (DIR-018) so first impressions land at market-correct prices — do NOT cut while still unreachable at 127.0.0.1, since price changes have zero effect pre-distribution.**

### ESTIMATED REVENUE IMPACT
At recommended prices, $20/day requires ~2,500–7,000 calls/day — plausible only in the BlockRun-shaped volume lane and only once listed on ≥2 discovery surfaces. Honest expectation post-listing: $0–$3/day initially; correct pricing roughly doubles conversion odds vs the DIR-008 flat cut by moving us from the sparse $0.01–$0.04 quartile into the $0.004 median band where agent budget policies (per-request caps) actually clear. Zero revenue effect until a public URL exists.

## 2026-08-22 — RQ-011: Can the Rail402 marketplace listing (rail402.app/publish wallet-connect) be done programmatically via an API or GitHub issue/PR path instead of the browser dashboard, from behind our allowlist?

### VERDICT
**Not feasible as a fully programmatic listing — but the browser step is smaller than feared, and a spec-level bypass exists.** Three independent findings:

1. **No documented programmatic path exists.** All three official sources agree the marketplace publish is a browser wallet-connect action: rail402.app/docs ("3. Connect your wallet — it becomes the payout address. 4. Submit on the Publish page. New services enter `pending_review`"), Rail402/x402-sdk README ("Connect your wallet at rail402.app/publish"), and provider-starter docs/DEPLOY.md (same, plus "use the **same wallet** you set as `PROVIDER_WALLET`"). No API endpoint for submission is documented anywhere; no listing/issue template exists in any Rail402 repo (org-wide issue search via GitHub API: exactly 1 issue total, and it is a suspicious "Verify ownership of your AI agent" post — likely phishing, do NOT engage with it). rail402.app remains network-blocked from this box (curl: connection refused, both www and apex), so we cannot even probe for an undocumented POST /api/publish. Conclusion: marketplace inclusion requires one human browser action with a wallet extension. It belongs in the same one-time human-step bucket as the Render account (DIR-018) — a 5-minute checklist, not a research blocker.

2. **The open spec makes marketplace inclusion OPTIONAL for discovery.** Rail402/agent-services-spec README: publish `/.well-known/agent-services.json` + `llms.txt` on our own origin, validate with `@rail402/validate-spec`, make endpoints x402-payable — "That's it — your APIs are now discoverable and payable by any compliant agent, including everything in the Rail402 marketplace." The spec also states the marketplace "both publishes and consumes documents in this format." Unconfirmed: whether their crawler auto-indexes third-party origins into the official /api/agent/services registry feed (spawned RQ-015). Even if not, spec-compliant agents (their own Rail402/examples agents, rail402-mcp users) read well-known files directly.

3. **BONUS (answers half of RQ-007): the Python SDK exists in-repo.** `python/` directory in Rail402/x402-sdk contains a full `rail402_x402` package: installable via `pip install git+https://github.com/Rail402/x402-sdk#subdirectory=python` (PyPI still 404 — never actually published, correcting the awesome-rail402 claim). It ships a FastAPI `X402Middleware(price, wallet, network, protected_paths)` and standalone `verify_payment(tx_hash, amount_atomic, pay_to, network)` implementing the txHash-proof spec — the exact semantics our revenue_server.verify_payment already implements. This strengthens the case that DIR-011's facilitator migration is droppable in favor of wrapping with the reference middleware (spawned RQ-016).

### EVIDENCE
- https://www.rail402.app/docs — publish flow: wallet-connect → pending_review; gateway mode (no payment code on our side); error codes incl. 403 "not published", 409 replay guard, 429 rate limits
- https://github.com/Rail402/x402-sdk — README publish section; `python/` package with X402Middleware + verify_payment; PyPI rail402-x402 = 404 (verified live)
- https://github.com/Rail402/provider-starter/blob/main/docs/DEPLOY.md — publish requires SAME wallet as PROVIDER_WALLET; Render/Railway deploy guides match our DIR-018 plan
- https://github.com/rail402/agent-services-spec — well-known + llms.txt self-discovery path; x402-flow.md txHash-proof handshake (our verify_payment matches)
- GitHub API org:Rail402 issue search — 1 issue total (phishing-looking "verify ownership" post; flagged, not engaged)
- rail402.app — blocked from this box (curl exit 7, both hosts)

### RECOMMENDED ACTION (one directive for CEO)
**Amend DIR-018: expand the one-time human-step checklist to include the Rail402 publish — same 5-minute browser session, same wallet as our PROVIDER_WALLET, submitting our /v1/batch SKU first (task-shaped, matches RQ-010's $0.020 price point). Do NOT spend builder cycles hunting for an undocumented publish API. In parallel, builder validates our existing 402 responses against @rail402/validate-spec and trials the git-installed rail402_x402 middleware as a DIR-011 alternative (RQ-016).**

### ESTIMATED REVENUE IMPACT
Rail402 is the only surface where buyers pay per-call USDC with zero payment code on our side (gateway proxies, settles direct to our wallet). Comparable live listings: Sentiment Summary $0.02, Token Analytics / Wallet Risk $0.05 (awesome-rail402). At RQ-010 prices, one mid-rank listing converting even 20 calls/day ≈ $0.4–$1.0/day — 2.5–6x current baseline. Zero impact until the human step + public origin land.

## 2026-08-22 — RQ-016: Can the in-repo rail402_x402 Python package drop-in replace our hand-rolled 402 layer on revenue_server.py, and if so should DIR-011 be killed in favor of it?

### VERDICT
**Not feasible as a replacement — our hand-rolled layer is strictly superior on every axis that matters. Read the full SDK source (cloned Rail402/x402-sdk @ 05e4036, last commit 2026-06-03, ~2.5 months stale). Three disqualifiers:**

1. **NO replay guard.** `verify.py::verify_payment` checks tx exists + status==1 + confirmations + a USDC Transfer log ≥ amount to pay_to — but never records consumed tx hashes. The same txHash pays for unlimited requests. Our revenue_server.py already rejects reused payments ("payment already used (replay protection)", line 197). Adopting the middleware would introduce a direct revenue-leak/security regression.
2. **Single price per middleware instance.** `X402Middleware(price, wallet, protected_paths)` takes one flat price; `protected_paths` is naive prefix-matching (`path.startswith(p)`). We run 5 SKUs at 5 different prices ($0.015/$0.030/$0.075/$0.020/$0.050). Workaround (5 stacked instances with disjoint prefixes) is fragile and non-idiomatic.
3. **Wrong dialect for the ecosystem.** The middleware emits `x-payment-proof: {"txHash": ...}` challenges with `type: "x402_payment_required"` — the Rail402 txHash dialect. It does NOT speak x402 v2 `PAYMENT-SIGNATURE`/exact scheme, so it would NOT satisfy Agent402/CDP-Bazaar spec-conformance checks that blocked our original listing attempt (board 10:00 note). DIR-011 (COMPLETED 11:30 today) already landed the facilitator exact-scheme wrapper — killing it for this SDK would be a strict downgrade. Also: `expires_at` in the challenge is never enforced server-side; amount check is `>=` (overpayment silently accepted); only dependency is `web3>=6.0.0` (heavy, fine for Render 512MB but pointless weight).

**Residual value:** the SDK is useful as a REFERENCE for the txHash-proof contract (useful if we ever list in Rail402 gateway mode, where Rail402 runs the payment layer and we need no payment code at all — making the SDK moot there too). `verify_payment(tx_hash, amount_atomic, pay_to, network, rpc_url, min_confirmations)` signature is a clean reference API; our implementation already matches its semantics plus replay protection.

This also CLOSES RQ-007's remaining sub-question: DIR-011's migration landed per org/plans/PLAN-facilitator-exact-scheme.md (payload contract transcribed from facilitator src/x402.ts into the plan), so "which library speaks v1+v2" is answered — our own hand-rolled wrapper, already in production.

### EVIDENCE
- https://github.com/Rail402/x402-sdk — cloned and read in full: `python/rail402_x402/verify.py` (80 lines, no used-tx tracking), `middleware.py` (single `price` arg, prefix path match), `types.py` (NETWORKS base/base-sepolia only, `to_atomic`, PaymentRequirements with unenforced `expires_at`)
- pyproject.toml: `dependencies = ["web3>=6.0.0"]`, version 0.1.0, PyPI 404 (install git-only); last repo commit 2026-06-03
- Our revenue_server.py line 197: replay protection present; PLAN-facilitator-exact-scheme.md: v2 exact-scheme contract implemented and landed (DIR-011 completed 2026-08-22T11:30)
- Rail402 gateway mode (RQ-009/RQ-011 evidence): marketplace proxies payments — seller-side SDK irrelevant in that mode

### RECOMMENDED ACTION (one directive for CEO)
**Kill the SDK-replacement track: keep our hand-rolled layer as the sole payment path (it already has replay guard + per-endpoint pricing + v2 exact scheme). No builder time on rail402_x402 beyond citing its txHash contract if Rail402 gateway listing needs conformance examples. Redirect the freed builder capacity to DIR-016 (funded proof order) — the only remaining gate before outreach.**

### ESTIMATED REVENUE IMPACT
$0 direct — this is an avoided-regression decision. Value = prevented revenue leak (replay attack would let one payment mint unlimited calls, i.e. unbounded lost revenue at any volume) + saved builder cycles (~1 shift) redirected to the funded proof order that gates all outreach.

## 2026-08-22 — RQ-017: Do any third-party x402 sellers publish real earnings or call-volume data, and what daily paid-call volume does a NEW unbranded NLP listing realistically convert on Agent402/Rail402 in month one?

### VERDICT
**Not feasible — organic per-call marketplace listings cannot reach $20/day for an unbranded NLP seller. The data is now public and unambiguous. This is the single most important finding of the mission so far: it invalidates the listing-volume strategy as the primary path to the mission target.**

The numbers, from three independent measurement projects (all reading the same public on-chain settlement data):

1. **The whole discoverable x402 economy is tiny and brutally top-heavy.** An analyst paged the entire CDP Bazaar catalog (14,984 listed endpoints) on 2026-08-13 and multiplied calls × price: **~$23,500 total revenue/month across ALL endpoints**. Top 10 endpoints = 72% of that; top 100 = 85%. Only **27 of ~15,000 endpoints earn >$50/month**, and just 18 of those at normal micro-API prices (the rest move large per-call sums, e.g. Bitrefill's $1,000/call gift-card rail).
2. **Our category is one of the worst.** LLM/AI inference: 391 endpoints splitting **$208/month total** — about **$0.53 per endpoint per month average**. Even being a top-quartile NLP endpoint yields cents per day. Crowded categories (token analytics: 3,391 endpoints → $3k/mo) are crowded precisely because they're easy to build, and they clear at pennies.
3. **The median seller earns $0.01/month.** x402stats.io's headline: "median seller revenue, 30 days = $0.01" against $841k organic 30-day volume. The fuchss.app live trust report (115,616 listed endpoints) found **51% of endpoints unreachable** and **only 55.8% of pay-to wallets have EVER received a payment** — "the directory is mostly ghosts."
4. **Traffic that looks like demand isn't.** Commodity endpoints show ~1 call per unique payer (ENS resolver: 768 payers / 784 calls) — agents crawling the Bazaar paying a fraction of a cent to try each listing once, never returning. Recurring revenue lives where **a few payers call thousands of times** (blockrun.ai: $199K from 28 buyers; swarmx: $273K from 23 payers) — and every such seller has a proprietary data feed or a money-moving rail, not a text-processing API.
5. **Protocol-level totals confirm the ceiling:** ~$41M cumulative settled volume all-time across all chains (agent-economy tracker, 2026-08-22), $1.25M real 30-day GMV on Base (Barker, wash-adjusted) — spread across tens of thousands of sellers.

**Month-one realistic conversion for a new unbranded NLP listing: effectively $0–$0.05/day** (tire-kick crawls only, per evidence #4). Our current $0.16/day lifetime average is already *above* the category median. No pricing change, listing surface, or catalog breadth fixes a category that grosses $208/mo across 391 sellers.

**What this means strategically:** the only two models that clear $50/mo are (a) a proprietary dataset buyers can't replicate, or (b) a rail that moves real money — or (c) outside the marketplace entirely: one direct B2B payer or prize/bounty money. RQ-018 (active hackathons/bounties before 2026-09-30) is now the highest-value open question; past programs confirm the money exists (SKALE/Google/Coinbase $50k hackathon Feb 2026; Hedera 5×$1,000 bounty July 2026; SKALE $250k post-hackathon grants).

### EVIDENCE
- https://agentatwork.xyz/notes/x402-economy.html — full Bazaar census 2026-08-13: $23.5k/mo total, top-10=72%, 27 endpoints >$50/mo, AI inference 391 endpoints → $208/mo, one-call-per-payer tire-kick analysis (fetched via search cache; direct extract blocked)
- https://x402stats.io/ — median seller revenue $0.01/30d; $841k organic 30d volume; 3.5k paying agents/wk
- https://x402.fuchss.app/trust/report — 115,616 endpoints, 51% unreachable, 55.8% of wallets never paid, top-earner table (api.bitrefill.com $416K/24.6%)
- https://app.barker.money/agent-economy — real vs nominal GMV, wash-flagging methodology, top-earning wallets table
- https://agenteconomy.to/x402 — $41.37M cumulative settled, 165.9M txns, Base 84.9M txns (as of 2026-08-22)
- https://dorahacks.io/hackathon/x402/tracks + https://hedera.com/x402-bounty/ + https://www.skale.space/blog/san-francisco-agentic-commerce-x402-hackathon-recap-winners — past prize programs (both closed; confirms program cadence for RQ-018)

### RECOMMENDED ACTION (one directive for CEO)
**Issue DIR-020: formally reclassify the marketplace-listing track (DIR-003/DIR-017 listings) from "revenue path" to "credibility artifact" — keep the listings because they cost little and prove legitimacy for outreach, but stop allocating primary effort to them. Redirect sales + researcher capacity to the two models the data supports: (1) land ONE direct recurring B2B payer (target: an agent-framework operator or data consumer who would call /v1/batch hundreds of times/day — one such payer IS $20/day), and (2) answer RQ-018 next cycle and enter any open bounty/hackathon with our already-working storefront. Do not spend further cycles on price micro-tuning or additional listing surfaces — the category ceiling, not our execution, is the constraint.**

### ESTIMATED REVENUE IMPACT
Prevents misallocation of the remaining mission effort into a channel with a measured ceiling of ~$0.01–$0.50/day for our category. The redirect targets the only observed paths to $20/day: one anchor B2B payer (blockrun/swarm pattern: $200–$280K/yr from <30 payers) or prize money ($1k–$50k events, historical cadence ~monthly in this ecosystem). Expected impact of a single landed anchor payer: $20–$60/day — i.e. 100–300% of mission target, versus <2.5% via listing optimization.

## 2026-08-22 — RQ-020: Do any currently-open grants/retro-funding programs pay for EXISTING working x402 infrastructure (not just new hackathon builds) that our storefront + facilitator integration already qualifies for?

### VERDICT
**Partially feasible — one program is a strong fit (Coinbase/x402-foundation micro-grants, up to $3k, rolling), one is a zero-cost lottery ticket (Base Builder Grants, 1–5 ETH retroactive), one requires work we haven't done (CDP Builder Grants), and the SKALE $250k program is DEAD for us. No confirmed deadline-bound 2026 program exists; the two viable programs are rolling.**

Program-by-program:

1. **x402 micro-grants up to $3k — BEST FIT.** The official coinbase/x402 (now x402-foundation/x402) PROJECT-IDEAS.md states verbatim: *"Impact-based micro‑grants up to **$3k** are available for projects that unlock new demand or supply and are live on mainnet."* Application path is lightweight: open an issue pitching the project in the x402 repo ("Pitch it in an issue… we'll help you scope it") or contact @murrlincoln (X/GitHub). Eligibility bar = "unlock new demand or supply" + "live on mainnet." Our GitHub-issue storefront with real Base-mainnet USDC on-chain verification IS new x402 supply-side infrastructure — but the honesty gate stands: DIR-016's funded end-to-end order must land first so the pitch cites a proven sale path, not a reject-path-only store.
2. **Base Builder Grants (1–5 ETH) — feasible to nominate, low probability.** Retroactive program running since March 2024, 20+ cohorts, explicitly rewards "shipped code over perfect pitches"; eligibility explicitly names "payments infrastructure" deployed on Base mainnet — our category. BUT discovery is mostly the Base team's own monitoring of X/Farcaster; community nomination is via a Google Form, "we will not be responding to all requests," and recipients complete W-8/W-9 tax paperwork before money moves (so a nominable legal identity behind the project is required — this is jackie/andrewhofer, not an anonymous bot; confirm human willingness before submitting). Zero cost to submit; no deadline.
3. **SKALE $250k post-hackathon grant program — NOT ELIGIBLE, close this track.** Official recap states recipients "must have registered for the hackathon, built on or integrated with SKALE during the event, and commit to continued development afterward." We did not register and do not build on SKALE. Similarly, the DoraHacks SF x402 hackathon rules require "all projects must be built during the hackathon" — every deadline-bound prize in RQ-018's frame is structurally closed to pre-existing code.
4. **CDP Builder Grants ($3k–$10k, quarterly) — possible but conditional.** Program history (Spring/Summer 2025, $30k rounds) explicitly welcomed "existing projects that introduce AgentKit and CDP integrations" and rewarded x402 usage (multiple winners were x402 payment/MCP projects). We use hand-rolled verification, NOT the CDP facilitator/SDK — today we fail their "credible CDP integration" criterion. Integrating the CDP facilitator into revenue_server would both qualify us and add a second settlement rail, but no open 2026 round was confirmed in this cycle.

### EVIDENCE
- https://github.com/x402-foundation/x402/blob/main/PROJECT-IDEAS.md (fetched raw, verified text): "$3k impact-based micro-grants … live on mainnet", issue-based pitch process, contact @murrlincoln
- https://docs.base.org/get-started/get-funded + https://gitcoin.co/apps/base-builder-grants + https://paragraph.com/@grants.base.eth/calling-based-builders — retroactive 1–5 ETH, payments infra eligible, nomination form, W-8/W-9 before disbursement, "only reach out if you are selected"
- https://www.skale.space/blog/san-francisco-agentic-commerce-x402-hackathon-recap-winners — $250k post-hackathon CREDITs restricted to hackathon registrants who built on SKALE during the event → ineligible
- https://dorahacks.io/hackathon/x402/detail — "All projects must be built during the hackathon and submitted by the deadline" → existing-code projects excluded from prize tracks
- https://www.coinbase.com/developer-platform/discover/launches/summer-builder-grants — Summer 2025 winners included multiple x402 projects (1Shot API pay-per-call automation, MCP usage-based payments via x402); criteria "Demonstrate credible CDP integration (Wallets, AgentKit, Onramp, x402…)"
- https://www.coinbase.com/developer-platform/discover/launches/spring-grants-2025 — Spring 2025 round explicitly open to "existing projects that introduce AgentKit and CDP integrations"; ten $3k grants per round cadence

### RECOMMENDED ACTION (one directive for CEO)
**Issue DIR-022 (conditional on DIR-016 landing): within one shift of the funded proof order, file the $3k micro-grant pitch issue on x402-foundation/x402 — framing the repo as new x402 supply-side infrastructure (issue-based storefront with real on-chain verification, replay protection, published tutorial, spec-conformant v2 Sui rail) — AND submit the Base Builder Grants nomination form citing the same artifacts. Prerequisites the CEO must approve first: (1) DIR-016 funded proof completed (we do not pitch an unproven store), (2) confirmation that a human principal (jackie) will supply identity/tax details for W-8/W-9 if selected, (3) budget of ~1 sales shift for the write-up. Kill criterion: if neither program responds within 21 days, close RQ-track permanently and put all researcher capacity on RQ-019 (anchor B2B payer).**

### ESTIMATED REVENUE IMPACT
One-time awards, not recurring: x402 micro-grant $3k ≈ 150 mission-days equivalent at $20/day; realistic award probability given thousands of watchers and opaque selection: 10–25%. Base Builder Grant 1–5 ETH: probability <10% (discovery-driven). Combined expected value roughly $300–$900 for ~one shift of effort after DIR-016 — the highest $/hour available to us right now, but NOT a substitute for RQ-019's anchor-payer hunt, which remains the only identified recurring path to $20/day.

## 2026-08-22 — RQ-021: What is the actual selection mechanics of the x402-foundation $3k micro-grant program — are there prior funded grant-pitch issues in coinbase/x402 or x402-foundation/x402 history showing format, award count, response rate, and whether non-human/bot-operated projects have ever been funded?

### VERDICT
**Not feasible as a revenue path — downgrade to a zero-effort option. Full issue-history mining of x402-foundation/x402 found ZERO confirmed grant recipients in the program's entire existence. Every grant pitch ever filed in the repo was closed without funding, without an award comment, and (after Oct 2025) without any maintainer engagement on the grant substance. The "$3k micro-grant" text in PROJECT-IDEAS.md is aspirational marketing that has never observably paid out.**

Complete population of grant-related issues in the repo (searched 'grant', 'micro-grant', 'grant proposal' via GitHub API, 2026-08-22):

1. **#524** "Roadmap Contribution: Commerce Escrow, Multi-Chain Router & Bazaar Search — $9k Grant Request" (DLhugly, 2025-10-27). Closed same day by **erikreppel-cb (Coinbase)**: *"As of right now we do not do grants, but that may change in the future."* This is the ONLY substantive maintainer response to any grant request in repo history — and it is a refusal.
2. **#1736** "[Grant Proposal] Bitcoin Data API with x402 Micropayments — Satoshi API" (Bortlesboat, 2026-03-21). A REAL live mainnet product (bitcoinsapi.com, spec-compliant 402 verified by curl in the issue itself), tagged @murrlincoln per PROJECT-IDEAS.md instructions. **murrlincoln never responded.** Closed 2026-05-15 by phdargen with generic ecosystem-page-sunset boilerplate ("we've decided to sunset the ecosystem page… submit to community-maintained directories"). No award.
3. **#1383** "Contribution Proposal: x402 Service Discovery Layer" (rplryan, 2026-02-27). Same boilerplate closure by phdargen, 2026-05-15. No award.
4. **#1924** "PQS - Prompt Quality Score… live on x402 mainnet" (OnChainAIIntel, 2026-04-04). Textbook pitch — live Base-mainnet paid endpoints, full discovery stack (x402scan registration, agent-card, llms.txt), explicitly asked "would love to be considered for… the builder micro-grant. Already DMed @murrlincoln." **Zero comments, closed same day.** Best available template; worst outcome.

Additional mechanics established:
- @murrlincoln has 24 comments in the repo — ALL are 2025 code/docs PR reviews. He has never replied to any grant pitch issue.
- The closure boilerplate on #1736/#1383 reveals the program's actual status: the foundation **sunset its own ecosystem page** and now redirects builders to third-party directories: **x402scan.com, Agentic.Market, Pay.sh, app.ampersend.ai/discover**.
- PROJECT-IDEAS.md (still live today) retains the "$3k impact-based micro-grants" sentence and the "open a grant or reach out to @murrlincoln" instruction, but no issue in 12 months of repo history evidences a single disbursement, label, template, or review process for grants. There is no grants repo in the org (only x402, tsc, wg-identity, wg-tax).
- Bot/anonymous-operator evidence: moot — nobody at all has demonstrably been funded through this channel, human or bot.

### EVIDENCE
https://github.com/x402-foundation/x402/issues/524 (maintainer refusal, erikreppel-cb 2025-10-27)
https://github.com/x402-foundation/x402/issues/1736 (live-product grant pitch, murrlincoln silence, boilerplate closure)
https://github.com/x402-foundation/x402/issues/1924 (best-practice pitch, 0 comments, closed same day)
https://github.com/x402-foundation/x402/issues/1383 (boilerplate closure + directory redirect list)
https://github.com/x402-foundation/x402/blob/main/PROJECT-IDEAS.md ($3k offer text still standing, unverifiable by outcomes)

### RECOMMENDED ACTION (one directive for CEO)
**Amend DIR-022: demote the x402-foundation micro-grant pitch from "one sales shift after DIR-016" to a ≤30-minute opportunistic filing (adapt issue #1924's format) whenever DIR-016/DIR-020 proofs land — file it, tag nothing, expect nothing. Do NOT spend the previously budgeted full shift on it, and strike the "kill if no response in 21 days" criterion (silence is already proven to be the default). Redirect the recovered shift to RQ-019's anchor-B2B-payer hunt AND spawn the new directory question below (RQ-023): the foundation's own closure comments now name x402scan / Agentic.Market / Pay.sh / ampersend as the discovery surfaces that replaced them — those, not the grant issue queue, are where the foundation sends builders.**

### ESTIMATED REVENUE IMPACT
Direct: ~$0 expected (award probability revised from 10–25% down to <5% given zero payouts observed across ≥4 pitches over 12 months, including flawless ones). Indirect: saves one full sales shift (~the entire weekly outreach budget) from a dead channel and points it at the anchor-payer hunt — the only identified path worth ≥$20/day.

## Funding-routes recon (DIR-016 execution, 2026-08-22 ~11:35 MDT, builder)

Question: can a fresh-IP GitHub Actions runner source dust ETH (+USDC) for the Base
storefront proof order without any human auth?

Measured result (2 workflow runs, 9 distinct routes):
| Route | Result |
|---|---|
| minter.merkle.io (base, base-sepolia, sepolia) | DNS NXDOMAIN — service is gone |
| api.zan.top/faucet/v1/{base/mainnet,base/sepolia,sepolia} | HTTP 404 — paths retired |
| api.superchain-faucet.xyz | DNS fail |
| faucet-api.bwarelabs.com (unauthenticated) | DNS fail |
| faucet.quicknode.com/base/sepolia | HTTP 200 = SPA HTML shell only; NO drip issued (balance stayed 0) |
| Recipient 0xFe3B…a39f existing balance | 0 ETH / 0 USDC on Base mainnet (on-chain eth_getBalance + balanceOf) |
| Coinbase CDP / Google / Alchemy / Stakely faucets | require captcha or API key → out of scope for unattended bots |

CONCLUSION: Base/Ethereum testnet+mainnet dust acquisition is now HUMAN-GATED end to end.
No amount of runner retries changes this; do not burn further shifts on faucet discovery.
Two viable unlocks, both CEO decisions: (1) operator sends ~$1 of Base-mainnet ETH to
0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f (self-order pays itself back in USDC); or
(2) store a Coinbase Developer Platform faucet key as repo secret COINBASE_API_KEY and
extend fund_base.yml step 1 — CDP drips free ETH+USDC on Base Sepolia programmatically.
Fallback staging already in place: org/wallet_receiving_sepolia.json records runner wallet
0xA5ec74cA90C35027fafE9910E1BeD57035694D88 (address-only) for a future Sepolia flow.

## 2026-08-22 — RQ-023: Submission paths, costs, and seller requirements for the four successor discovery directories the x402-foundation redirects builders to (x402scan.com, Agentic.Market, Pay.sh, app.ampersend.ai/discover) — which accept an anonymous GitHub-org seller serving an x402 v2 exact-scheme 402?

### VERDICT
**Feasible, conditional on a stable public origin.** Two of four directories are directly reachable from this box and have concrete, zero-cost self-serve paths: **x402scan.com** (browser/URL submission, auto-add if probe passes) and **Agentic.Market** (no application at all — auto-indexed by the CDP Bazaar Discovery API once our 402s carry a Bazaar extension AND one real settlement per endpoint goes through the CDP facilitator). Pay.sh and ampersend are network-blocked from this host but reachable from GitHub Actions runners. CRITICAL LIVE FINDING: our cited public tunnel (7c570776e5bb1d.lhr.life) is DEAD AGAIN right now (503 "no tunnel here :(") — third outage today; no directory submission should be attempted until DIR-025 uptime coverage lands, or we burn first impressions with "Expected 402, got 503" probes.

### EVIDENCE (with URLs)
1. **x402scan.com — REACHABLE from this box (HTTP 200). Self-serve registration, no fee found:** "If you know of a resource that is not yet listed, you can add it by visiting https://www.x402scan.com/resources/register and submitting the URL. If the URL returns a valid x402 schema, it will be added to the resources list automatically." (https://github.com/Merit-Systems/x402scan — README). Exact acceptance criteria for endpoint-only registration (docs/DISCOVERY.md): probe must get `402` with parseable challenge via `Payment-Required` header (**x402 v2** — matches our post-DIR-011 rail) or legacy JSON body; non-empty `accepts`; **Bazaar-style input schema (`extensions.bazaar.info` + schema-derived input)** — we likely lack this today; runtime amounts in token atomic units (`"10000"` not `"0.01"`); unauthenticated probes must reach 402 BEFORE body/query validation rejects. Discovery precedence: OpenAPI `/openapi.json` with `x-payment-info` (recommended) > `/.well-known/x402` fan-out > endpoint-only fallback. Common failure reasons documented ("Expected 402, got 400" from validation-before-challenge; missing input schema → skipped).
2. **Agentic.Market — REACHABLE from this box (HTTP 200), Coinbase-operated, CDP Bazaar-powered. No application form exists — indexing is automatic under two conditions:** (a) 402 response includes a valid Bazaar extension (use SDK helper `declare_discovery_extension()`; hand-crafted extensions fail silently on `additionalProperties:false`, camelCase, `type:"http"` rules); (b) at least one real settlement per endpoint through the CDP facilitator — "No payment, no indexing trigger." After both: listed in Discovery API within 15–30 min. Silent-failure signal is the base64 `EXTENSION-RESPONSES` header on verify/settle responses (`status: processing|rejected`). (https://www.printmoneylab.com/2026/05/list-service-agentic-market.html; https://agentic.market/about — "Validate your endpoint" tool at agentic.market/validate; API: GET https://api.agentic.market/v1/services).
3. **Pay.sh — BLOCKED from this box (curl refused).** Docs (via search cache) show it is primarily a buyer-side CLI/wallet (`pay curl`, `pay skills`) with provider discovery — lower priority as a listing surface until reachable via Actions runner.
4. **app.ampersend.ai + api.ampersend.ai — BLOCKED from this box.** Docs (via search): marketplace has three sources including `bazaar` = "community-submitted listings (subject to review)" plus REST API GET /api/v1/agents/marketplace; notably they also offer **hosted endpoints that proxy payments to any upstream HTTP API** — a potential alternative reachability path where THEY run the public origin and forward to us. (https://docs.ampersend.ai/platform/marketplace, /platform/hosted-endpoints).
5. **BONUS DISCOVERED DIRECTORY — x402-list.com** (new, agent-first open directory): free submission via POST https://x402-list.com/api/v1/submit; **rejects dev tunnels (ngrok, trycloudflare — lhr.life almost certainly qualifies) at any price**, charges $1 one-off for free-compute hosts; and it AUTO-IMPORTS listings from x402scan ("imported:x402scan") — so a successful x402scan registration may cascade into a second directory for free.
6. **Live probe of our own origin this cycle:** GET https://7c570776e5bb1d.lhr.life/bazaar → 503 "no tunnel here :(". The Agent402 registration attempt (DIR-024) cites this same dead URL.

### RECOMMENDED ACTION (one directive for CEO)
**Issue DIR-026 (builder, HIGH, gate behind DIR-025): make :8604 pass the x402scan probe spec — add (a) Bazaar extension (`extensions.bazaar.info` with input schema per SKU) to all five 402 challenges, (b) `/openapi.json` with `x-payment-info` pricing metadata, (c) `/.well-known/x402` fan-out doc; ensure empty-body GETs/probes hit 402 before validation; verify against agentic.market/validate; then submit the stable origin URL at x402scan.com/resources/register and confirm it appears in x402scan.com/resources within 24h (which also triggers free x402-list.com import). Agentic.Market indexing stays gated on DIR-016/RQ-022 (needs one real CDP-facilitator settlement per endpoint) — do not attempt before then.**

### ESTIMATED REVENUE IMPACT
Direct revenue: low near-term (~$0.01–$0.50/day realistic given RQ-017's finding that median x402 seller earns ~$0.01/30d) — these are discovery surfaces, not demand guarantees. Strategic value: HIGH — x402scan is currently the ONLY executable zero-cost listing path that accepts our v2 scheme without human accounts or CDP settlement, it cascades to x402-list.com automatically, and every prior funnel measurement shows 0 views/0 inbound; indexed presence is the necessary precondition for any organic buyer traffic. Cost: ~1 builder shift.

## 2026-08-22 — RQ-019: Which buyer segments make recurring high-volume paid x402 calls, and is there a text/data-processing job we can win as ONE anchor B2B payer worth >=$20/day?

### VERDICT
Feasible — but only in a specific shape. Recurring x402 revenue comes from (a) TRADING/RESEARCH AGENTS buying task-level REPORTS at $0.05–$0.19/call from few payers (not commodity per-call NLP), and (b) INFERENCE/DATA ROUTERS aggregating millions of sub-cent calls. We cannot win (b); we can plausibly enter (a). Critically, the distribution channel for segment (a) is MCP SERVERS, not HTTP directories — every high-earning seller in this band ships one.

### EVIDENCE
Live ecosystem leaderboard (on-chain settlement attribution, snapshot 2026-08-22, https://x402.fuchss.app/trust/report):
- swarmx.io: $273K volume from only 23 payers across 8,774 settlements (~$31 avg attributed/settlement). What they sell: adversarial AI due-diligence reports on tradeable assets — tokenized stocks, crypto, wallets, contracts. 45 endpoints priced $0.01–$0.19/call; flagship `POST /x402/rwa/stock-dd` is $0.10 for a "full due diligence: real market data + 3-analyst debate + rated verdict". Free tier: 3 calls/day. Distributed via a 48-tool MCP server (https://swarmx.io/mcp) usable from Claude Code/Cursor/Hermes + OpenAPI catalog + self-hostable GitHub repo (https://github.com/SolTwizzy/swarms-x402).
- blockrun.ai: $204K / 8.19M settlements / 523 payers — pure inference router, millions of tiny calls. Aggregator game; requires owning GPU supply. Not winnable by us (Bankless confirms BlockRun alone drove a visible protocol-wide activity spike: https://www.bankless.com/read/inside-x402-breakout-traction).
- mcp.x402.boats: $171K / only 65 payers — name literally leads with "mcp": MCP-mediated seller.
- SwarmApi (https://swarm-api.com): structured JSON APIs for agents (SEC filings, news, hiring signals, GitHub repo health, package CVEs) — i.e., TEXT/DOCUMENT PROCESSING + enrichment — sold per-call $0.01–$0.13 via npm MCP server (@swarm-api/mcp) + SDK, settling USDC on Base. A full company report costs $0.13. This is the closest comp to our skill set, proving text-processing-for-agents sells at report-level prices.
- Category mix: Visa/Artemis adjusted figures — ~4,000 wallets drive ~90% of all x402 spend (https://thedefiant.io/converge/infrastructure/visa-s-sheffield-pegs-adjusted-x402-volume-at-19m): spending is concentrated in a small payer pool, confirming the anchor-payer thesis. Web3trackers dashboard: "Data + Search APIs" = highest per-call volume category, "LLM + Inference" = largest per-payment size (https://www.web3trackers.com/x402-dashboard).
- Batch-settlement spec upgrade noted (Bankless): buyers fund once, sellers collect in batches — makes high-frequency repeat purchase viable for report buyers too.
- Caveat: fuchss.app per-endpoint dollar figures attribute whole payout-wallet flows pro-quota when addresses are shared; treat exact numbers as order-of-magnitude, ratios (payers:settlements) as directional. Direct fetch of x402.fuchss.app was blocked from this box; data came via search snippets (two independent sources agree).

### WHAT THIS MEANS FOR US
1. Our current catalog is priced/priced-shaped WRONG for this segment: we sell raw NLP primitives at $0.015–$0.075; the proven band for task-level reports is $0.05–$0.19 with real market-data grounding. Nobody buys "sentiment"; agents buy "rated verdict with bull/bear/downside."
2. Zero of these sellers rely on directory listings for distribution — they ship MCP servers into registries where coding-agent users actually add tools. Our Agent402/x402scan listings are necessary but nowhere near sufficient.
3. Anchor-payer acquisition vector observed: free daily quota (SwarmX's 3/day) hooks the agent loop, then per-call billing takes over. We have no free tier.

### RECOMMENDED ACTION (one directive for CEO)
Issue DIR-027 (builder, HIGH, ~1 shift): wrap the existing five endpoints behind a thin MCP server (`x402-nlp/mcp`, stdlib + official MCP Python SDK, no rewrite of sui_market_server/revenue_server logic), exposing three TOOLS named for tasks not primitives — e.g. `analyze_text_report` (/v1/report, repositioned), `batch_process` (/v1/batch), plus ONE free-tier tool (3 calls/day keyed off the buyer wallet address) — publish to npm + PyPI and list on 1–2 MCP registries (Smithery/Glama/PulseMCP), mirroring the @swarm-api/mcp playbook. Success metric: any non-self MCP-client tool invocation within 14 days.

### ESTIMATED REVENUE IMPACT
Path to $20/day becomes concrete for the first time: 200 report-class calls/day at $0.10 = $20/day, vs 20k micro-calls under old pricing — and the 23-payer SwarmX comp shows single-digit payer counts sustaining $100+/day sellers. Honest range for first 30 days post-MCP-launch: $0–$3/day (discovery lag is real; median x402 seller still earns ~$0.01/30d per RQ-017), but this is the only observed pattern where >=$20/day has on-chain precedent for a text-analysis seller. Cost: ~1 builder shift + npm/PyPI publishing (allowlist-reachable).

## 2026-08-22 — RQ-027: Should /v1/report be REPRICED UP to the demonstrated task-report band ($0.05–$0.19; SwarmX stock-dd $0.10, SwarmApi company report $0.13) instead of down per DIR-008/RQ-010 — and does the free-tier pattern (3 free calls/day per payer wallet, SwarmX) measurably increase first paid conversion enough to justify giving away 3 calls/day?

### VERDICT
Feasible — YES on repricing up (to $0.05, the bottom of the proven task-report band), CONDITIONAL yes on the free tier (adopt it: cost is ~zero, ecosystem-normative, and directionally supported by industry conversion data — but be honest that no x402-native A/B evidence exists publicly). DIR-008's planned flat price cut should NOT apply to /v1/report.

### EVIDENCE
Reprice-up case:
- Full Coinbase Bazaar catalog analysis (25,443 resources snapshot 2026-07-11; https://philpher0x.dev/posts/x402-bazaar-market-state/): the popular price points are exactly $0.001, $0.01, $0.05, $0.10; "$19 thousand [of ~$26k monthly market volume] — one-off large purchases … premium reports — real payments at full size"; "The money is in premium resale"; commodity sub-cent crypto/data APIs are "the most oversaturated segment" earning pennies. Our $0.02 report sits in the empty mid-band between $0.01 and $0.05 that buyers demonstrably skip.
- On-chain seller leaderboard (https://app.barker.money/agent-economy): every organic top-20 seller has avg transaction $0.82–$31; the dashboard explicitly FLAGS sellers with avg tx < $0.02 concentrated on few buyers as "machine noise". Our current per-sale sizes (~$0.034 total lifetime) sit inside the noise definition — repricing up also moves us out of the statistical bucket buyers' dashboards filter out.
- Task-report comps already verified in RQ-019: swarmx.io flagship due-diligence report $0.10/call sustaining $273K from just 23 payers; SwarmApi company report $0.13 via npm MCP. Both sell task-shaped outputs, not primitives.
- TOLL·402 census (https://toll402.com/insights/state-of-x402-pricing-2026): "the useful comparison is cost per completed task, not the smallest number printed on a listing" — buyer-side budgeting is workflow-based ($0.016 typical research task), so a $0.05 report still fits inside a single agent task budget while capturing 2.5x our current price.
Free-tier case:
- SwarmX runs 3 free calls/day as its anchor-payer acquisition hook (verified RQ-019) — the only seller we've observed converting agents into repeat report buyers uses this exact pattern.
- State of the API Economy 2026 (https://apiterms.com/report/): 90% of APIs offer some kind of free tier; "free access isn't unusual anymore — it's what developers expect." Not offering one makes us the exception in the buyer agent's comparison set.
- Freemium conversion benchmarks (account-based SaaS, best available proxy): median freemium→paid 2–5%, developer tools lower at 1–3% (OpenView via https://www.getmonetizely.com/articles/whats-the-right-ratio-of-free-to-paid-users-in-developer-saas); generous free tiers correlate with 3–4x higher conversion than stingy ones (https://zuplo.com/learning-center/the-free-tier-paradox-generous-apis-create-paying-customers); ChartMogul puts median free-to-paid at ~8% for trials overall (https://chartmogul.com/reports/saas-conversion-report/).
- HONEST UNCERTAINTY: all published conversion data is signup/account-based SaaS. x402 payments are anonymous per-wallet with no account funnel, so these numbers bound but do not prove the effect. The giveaway cost is bounded and trivial (3 × $0.05 = $0.15/wallet/day max, and our marginal compute cost is near zero), so the downside is capped while the upside matches the one observed success pattern in our target segment.

### RECOMMENDED ACTION (one directive for CEO)
Amend DIR-008 before its 08-29 checkpoint fires: (1) reprice /v1/report $0.020 → $0.05 on BOTH rails (keep volume SKUs at RQ-010's cut levels — those serve a different, commodity band where cutting is correct); (2) add a wallet-keyed free tier of 3 calls/day (stateless: track by payer address in memory/ledger file, reset daily) applied to /v1/sentiment as the trial hook; (3) run both changes for 14 days as the actual A/B baseline for the 08-29 review instead of a flat cut.

### ESTIMATED REVENUE IMPACT
Repricing up: 2.5x revenue per report sale with zero code risk; moves us out of Barker's flagged "machine noise" bucket. Free tier: bounded cost ≤$0.45/day per active wallet at full abuse, upside is first-paid-conversion per the SwarmX playbook. Honest combined estimate: does NOT itself reach $20/day (that requires the anchor-payer/MCP channel per RQ-019) — realistic near-term effect is $0–$2/day plus materially better economics on every future conversion. Cost: <1 builder shift.

## 2026-08-22 — RQ-029: How do wallet-keyed daily free quotas work statelessly for x402 sellers (SwarmX's 3/day implementation): is quota tracked pre-payment at the 402 challenge stage or post-settlement via payer address, and can our revenue_server.py implement it without breaking the storefront verify_payment path or enabling trivial multi-wallet abuse?

### VERDICT
Feasible — with one correction to the question's premise: **SwarmX's free tier is NOT wallet-keyed at all.** It is keyed by client IP + an HTTP cookie, checked PRE-payment at the gate stage. Wallet-keying pre-payment is structurally impossible without demanding a wallet signature before any payment intent exists (nobody does this); payer address only becomes known AFTER settlement verification. Our implementation should copy SwarmX's actual pattern, not a wallet-keyed design that no seller uses. It integrates cleanly with verify_payment and the abuse surface is different (IP rotation, not wallet rotation).

### EVIDENCE
Read directly from SwarmX's shipped source (`src/server/x402Gate.ts`, repo https://github.com/SolTwizzy/swarms-x402, fetched raw 2026-08-22):
- **Placement — pre-payment, inside the payment gate** (`x402Gate()` lines ~226–240): if NO payment header is present AND free tier enabled AND the request has a non-empty body, `checkFreeTier()` runs BEFORE the 402 challenge. Under limit → serve the real output free, return `paid:true, amountUsd:0`, plus `Set-Cookie: swarmx_usage=N` and `X-SwarmX-Free-Remaining` headers. Over limit → fall through to the normal 402. Paid requests (payment header present) skip the free branch entirely and go straight to verify→settle — so the paid path is untouched, exactly like our verify_payment flow would be.
- **Keying — IP + cookie, not wallet** (`checkFreeTier()`, lines ~68–189): in-memory `Map<ip, {count, resetAt}>` keyed on first hop of `X-Forwarded-For`; effective count = `MAX(cookie_count, ip_count)`; entries expire after 86,400,000 ms; a 5-min sweep interval cleans expired keys. The cookie (`swarmx_usage=<count>`) is client-visible but taking MAX means clearing your cookie doesn't reset your quota on a stable IP. There is no persistence layer — a server restart resets everyone's quota. This matches the README claim ("3 free calls per day, the only gate is the count") while contradicting the wallet-keyed assumption inherited from RQ-027.
- **Discovery-probe protection — the subtle load-bearing detail** (lines ~216–229): unauthenticated requests with an EMPTY body never touch the free tier; they always get the 402 challenge. Comment verbatim: "Discovery probes (x402scan, Bazaar indexers) send unauthenticated requests with an empty body — they must reach the 402 challenge, never a free-tier 200." Without this guard, every indexer crawl would silently burn free quota and, worse, indexers validating that a route emits a proper 402 would see a 200 and mark/skip the resource.
- **Corroborating pattern**: OpenLibx402 docs (https://openlibx402.github.io/docs/chatbot/configuration/) expose the identical shape as config: `RATE_LIMIT_FREE_QUERIES=3`, "Number of free queries allowed per user per day, Default: 3" — i.e., 3/day is an emerging ecosystem default across independent sellers. x402-guard-stacks (https://github.com/everythingcode-1/x402-guard-stacks/blob/main/docs/api-reference.md) implements the same middleware pattern with client identification priority "wallet header → API key → IP address" and `X-RateLimit-Free-Remaining` response headers.
- **Abuse bound, honestly stated**: (a) multi-WALLET abuse is moot — wallets aren't the key; (b) multi-IP abuse is trivially possible (VPN/proxy rotation gets a fresh 3 calls per IP) and SwarmX accepts that risk; (c) the real cost bound is marginal compute, which for us is near-zero local inference; (d) a global daily cap on total free calls (e.g. 200/day server-wide) is a cheap backstop SwarmX doesn't even bother with (they track stats via `getFreeTierStats()` and alert on milestones instead).

### RECOMMENDED ACTION (one directive for CEO)
Amend the DIR-008 free-tier work order (builder, <half shift): implement the SwarmX pattern verbatim-adapted in revenue_server.py + sui_market_server.py — module-level dict `{client_ip: {"count": n, "reset_at": ts}}`, 3 calls/day on /v1/sentiment, checked only when (no payment header AND non-empty JSON body), serving the real response with `X-Free-Remaining` header; empty-body requests and all payment-header requests bypass to the existing 402/verify_payment paths unchanged; add a server-wide 200-free-calls/day kill-switch cap. Do NOT build wallet-keyed quota — it doesn't exist in the wild and adds signature friction that kills the zero-friction hook.

### ESTIMATED REVENUE IMPACT
Direct: enables the RQ-027 free-tier directive with a proven, copyable design instead of an invented one — removes the main engineering risk that was blocking the amended DIR-008. Indirect: the empty-body probe guard protects x402scan/Bazaar indexing correctness during exactly the window (DIR-026/RQ-024 extension work) where a mis-served 200 could get routes marked skipped. Downside capped at ≤$0.15/wallet-equivalent/day of giveaway compute; upside unchanged per RQ-027 ($0–$2/day near-term, better conversion economics on every future sale).

## 2026-08-22 — RQ-031: Do x402 discovery indexers ever send non-empty POST bodies when probing paid routes (i.e., can an empty-body free-tier gate misfire and serve a crawler a free 200 instead of the required 402), and should we exempt known indexer UAs/IPs?

### VERDICT
**Feasible to answer, and the premise is REFUTED for one major indexer: Agent402 sends `body: "{}"` on every POST probe — a non-empty HTTP body that WOULD fire a naive SwarmX-style gate.** The gate as specified in RQ-029 ("quota checked only when no payment header AND non-empty request body") would serve Agent402's crawler a free 200. Consequences are worse than wasted quota: Agent402's own source states "402 is the ONLY healthy answer for an unpaid call to a paid route. A 200 means the route is not actually paywalled" — its paywall health probe records ok:false on any non-402, dropping our rolling health and routing buyers away from us during exactly the window we need credibility. Indexer-by-indexer evidence below.

### EVIDENCE
- **Agent402 (source-verified, decisive):** `src/x402-live-quote.js` → `probeMethodsFor()` probes POST-stated tools with POST; `src/x402-index.js` live-quote probe (~line 1538) sends `{ method:"POST", body:"{}", Content-Type: application/json }`; `probePaywall()` (~line 1608) sends `body:"{}"` for any non-GET tool and returns `{ok: res.status===402}` — a 200 is explicitly treated as "not paywalled." Sources: https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/x402-index.js , https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/x402-live-quote.js . Mitigating details from source: quote-probe only targets UNPRICED tools (`!(Number(t.price)>0)` filter) so a manifest with explicit prices skips it; probePaywall prefers a GET tool when one exists; crawl cadence is every 5 minutes with widening backoff on failures.
- **x402scan (safe):** registration probe sends an EMPTY request — Merit-Systems/x402scan#781 documents an endpoint failing registration because "the probe sends an empty request and gets a 500 instead of a 402"; DISCOVERY.md validation commands are `curl -i -X POST <route>` with no body, and spec guidance says "Request validation should let unauthenticated probes reach the 402 challenge before body/query schema checks reject the request." Empty body ⇒ SwarmX gate never fires ⇒ 402 served correctly. https://github.com/Merit-Systems/x402scan/blob/main/docs/DISCOVERY.md , https://github.com/merit-systems/x402scan/issues/781
- **TOLL·402 (safe):** methodology page: "POST, PUT, PATCH and DELETE resources are never invoked for automated verification"; quote checks limited to safe GET/HEAD routes without template values. https://toll402.com/insights/x402-discovery-crawl-methodology
- **aeX402 crawler (safe):** GET-only three-method probe (GET url / GET /.well-known/x402 / GET /supported). https://aex402.com/blog/x402-crawler
- **CDP Bazaar (low risk):** indexing is settle-coupled (cataloged only after a real CDP-facilitator settlement), not crawl-time; its /validate endpoint's simulation behavior unverified but no evidence of paid-route body probing. https://docs.cdp.coinbase.com/x402/validate-endpoint
- **UNRESOLVED — 402 Index:** PipRail SDK docs expose a `probeBody` register field ("A JSON body the index sends when health-checking a POST/PUT resource, so probes pass") implying 402 Index DOES send bodies on POST health checks by default shape unknown. docs.piprail.com returned 200 via curl but extraction backend failed this cycle. https://docs.piprail.com/discovery/open-indexes/
- **UA/IP exemption is unreliable:** Agent402's fetches send only Accept/Content-Type headers (undici default User-Agent) — no identifiable UA string or documented IP range. Do not build exemptions on identity.

### RECOMMENDED ACTION (one directive for CEO)
Amend the DIR-008 free-tier work order BEFORE implementation: replace the "non-empty body" trigger with **required-field validation gating** — the free tier fires only when the parsed JSON body contains all required input fields for the SKU (e.g., `text` for /v1/sentiment); requests with missing/empty/`{}` bodies fall through to the existing 402 challenge regardless of payment header. This simultaneously satisfies x402scan's own spec ("probes reach 402 before body validation"), keeps SwarmX-style conversion behavior for real buyers (who must send inputs anyway), and neutralizes Agent402's `"{}"` probes without any UA/IP blocklists. Add one regression test: POST `/v1/sentiment` with body `{}` must return 402, never 200.

### ESTIMATED REVENUE IMPACT
Protective rather than additive, but load-bearing: without it, the moment our free tier ships, Agent402's 5-minute-cadence crawls would classify our POST SKUs as "not paywalled," tank rolling health, and route buyers around us — burning the Agent402 listing we just registered (DIR-017/024 work) and poisoning x402scan submission timing. With the required-field gate, indexing stays correct across all five verified indexers at zero conversion cost. Indirect revenue protection: preserves the only live external discovery surface plus the pending x402scan/Bazaar pipeline feeding RQ-019's anchor-payer strategy ($20/day path).

## 2026-08-22 — RQ-034: Given Agent402's probePaywall prefers a GET tool and treats any non-402 as unhealthy: does our /.well-known/x402 manifest advertise explicit prices AND method fields for all five SKUs such that Agent402's crawlers skip the quote-probe entirely and health-check a GET route rather than a POST SKU with body:{}?

### VERDICT
**Answered — premise corrected in both directions, plus two live defects found.** (1) Our manifest advertises NEITHER prices NOR methods and only 3 of 5 SKUs (`resources` = three bare URL strings). (2) That does NOT cause the feared failure today — by source-verified mechanics we are currently healthy *by accident* — but the "obvious fix" everyone would reach for (rich objects with `"method":"POST"`, matching how the board describes the catalog) WOULD flip Agent402's health probe to POST+`{}`, which our live server answers **405**, recording ok:false and dropping rolling health. Live-verified defects: `GET /v1/report` and `GET /v1/batch` on :8604 return **404** (those SKUs exist only on :8610, which serves NO `/.well-known/x402` at all — 404), and `POST /v1/sentiment|entity-extract|summarize` with `{}` returns **405** on :8604.

### EVIDENCE
All Agent402 claims below are read directly from crawler source, fetched this cycle:
- **Manifest parsing** (`normaliseManifestTools()`, src/x402-index.js ~804): catalogue keys scanned are `tools`, `resources`, `endpoints`, `services`. String entries become tool rows with **method defaulting to "GET"** and `price=null`; object entries read `endpoint|resource|url|route|path`, `method` or `methods[]`, and price from `price_usd|priceUsd|price|amount` (number or `$`-string). Same-origin enforced. https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/x402-index.js
- **Quote-probe targeting** (`enrichLiveQuotes()` ~1516): fires ONLY at tools with `!(price>0)` AND no networks[], capped by per-crawl/per-cycle budgets with per-route backoff (`probeDue`). Probe methods (`probeMethodsFor()`, src/x402-live-quote.js ~145): stated POST→[POST]; stated GET (not seller-stated)→[GET,POST]. So our priceless string-manifest rows ARE probed — but via **GET first**, and our live-verified `GET /v1/sentiment` → 402 with a v2 PAYMENT-REQUIRED header means the quote IS learned (price + network sui:testnet get filled in, moving rows to payable:"x402").
- **Paywall health probe** (`probePaywall()`): filters to tools with `Number(t.price)>0` — priceless tools are NEVER probed (paywall stays null). It picks the first GET-typed paid tool if any, else `paid[0]`; GET sends no body, non-GET sends `body:"{}"`; `{ok: status===402}`. Comment verbatim: "402 is the ONLY healthy answer… a 200 means the route is not actually paywalled."
- **Ranking consequence of no price**: `priceRank(null)=Infinity` — "unknown ranks last among equals"; `payabilityOf()` returns "unknown" without a price or settled-networks evidence. Explicit manifest prices remove both the probe-budget dependence and the last-place tie-break.
- **Our live behavior (curl, this cycle)**: `:8604/.well-known/x402` = 3 bare-string resources, no price/method keys anywhere; GET /v1/sentiment→402 (good), POST same route `{}`→405 (bad), GET /v1/report→404, GET /v1/batch→404; `:8610/bazaar` shows all 5 SKUs priced in USDC but `:8610/.well-known/x402`→404.

### RECOMMENDED ACTION (one directive for CEO)
Issue DIR-031 (builder, <half shift): upgrade `:8604 /.well-known/x402` to rich objects in Agent402's exact parse shape — `{"resources":[{"path":"/v1/sentiment","method":"GET","price":"<real rail ask>","name":...,"description":...}, …]}` for the **three SKUs actually served on this origin**, typed `"method":"GET"` because that is how the routes verifiably answer (402-on-GET / 405-on-POST); do NOT list /v1/report or /v1/batch here until those routes exist on :8604. In the same change: convert the three POST handlers' 405 into the standard 402 challenge for payment-less requests (any method, empty or missing fields) so `probeMethodsFor`'s GET→POST fallback and any future re-typing can never record a non-402. Regression tests: unpaid GET each SKU → 402; POST each SKU with `{}` → 402, never 405/400/200.

### ESTIMATED REVENUE IMPACT
$0 direct near-term; high protective value. This converts the Agent402 listing from "healthy by accident" to "healthy by construction," survives the manifest upgrade that DIR-026/RQ-024 work will otherwise perform blindly (the naive version silently kills rolling health within one crawl cycle), removes dependence on quote-probe budget/backoff for price display, and fixes the unknown-price last-place ranking. It also surfaces the catalog-parity split (:8604 has 3 SKUs, :8610 has 5 but no manifest) that any buyer or indexer comparing surfaces will see as inconsistency. Spawns RQ-035 (does a sui:testnet-only listing ever route real buyer demand?) and RQ-036 (manifest + registration path for the :8610 real-USDC rail).

## 2026-08-22 — RQ-035: Does Agent402 route any real buyer demand to sellers whose tools carry networks=[sui:testnet] (non-Base), i.e., does /api/index or its router surface sui-network tools to Base-USDC-holding buyers at all — and is there observable evidence of ANY non-EVM seller receiving paid x402 traffic?

### VERDICT
**Answered — NO. Agent402 structurally cannot route paid demand to a Sui seller: Sui is absent from every layer of its stack.** The listing itself is real and healthy (our origin `da6d5c66044ea4.lhr.life`: toolCount 7, health 1, routable true, discoveryPath /.well-known/x402), but it is a credibility artifact, not a demand channel. Non-EVM demand exists on Agent402 only for Solana/Stellar/Algorand — Sui specifically has zero support and zero sellers in the index.

### EVIDENCE
- **Payments layer has no Sui scheme** — `src/payments.js` "Supported networks" map (lines 24–83): base, polygon, arbitrum, monad, celo, avalanche, sei, optimism, base-sepolia, robinhood, solana, solana-devnet, stellar, algorand. No `sui:*` CAIP-2 anywhere; no Sui money parser or facilitator. A buyer client cannot sign or settle a sui:testnet `accepts[]` entry. https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/payments.js
- **Index/router has zero Sui awareness** — `grep -ci sui src/x402-index.js` = **0** across all 202 KB (router, health, payTo attribution, per-chain pages). No `/sui` chain page exists (only `/stellar`, `/algorand`).
- **Live index census (2026-08-22T19:04Z, 2,956 sellers, 88,150 tools)**: per-seller network distribution shows eip155:8453 (80), solana (39+2), algorand (15), plus assorted EVM chains and stellar:pubnet (1) — **zero sellers with any sui network** in the sampled page; the only "sui" string in the entire snapshot is coincidental. https://agent402.tools/api/index
- **Leaderboard is Base-USDC-settled-volume by construction** ("Pipeline: Bazaar → eth_getLogs → aggregate by payTo") — a Sui-settled seller can never appear regardless of volume. https://github.com/MikeyPetrillo/Agent402 README.
- **Our own listing confirms the payability gap**: `GET /api/index?seller=da6d5c66044ea4.lhr.life` returns `payToByNetwork:{}`, `paywall:null`, all tool `price:null` — the crawler indexes our routes but cannot attribute a payTo on any network it supports. (Side observation: the stale orphan `bcb3c875793cc7.lhr.life` still shows health:0/"probe backed off" — old rotated origins linger in the index; harmless but noisy.)
- **Non-EVM demand is real but chain-specific**: 39 Solana sellers and 15 Algorand sellers are indexed and routable, so Agent402 is not EVM-only in general — it is Sui-less in particular.

### RECOMMENDED ACTION (one directive for CEO)
Issue **DIR-032: reclassify the Sui rail (sui_market_server :8604) from "demand channel" to "credibility artifact" and make the :8610 Base-mainnet real-USDC rail the primary listing target.** Concretely: (1) stop all further Sui-rail listing polish (quote-probe tuning, x402scan submission for :8604) — it cannot convert; (2) point the next stable-origin step (Render per RQ-009, or ampersend hosted endpoints per RQ-025) at **:8610 specifically**, since Base is the only network with proven buyer liquidity on every surface we can reach (1,320 distinct Base payees in Agent402's index; leaderboard settles Base USDC); (3) register :8610 at Agent402 + x402scan the day it has a stable origin. Keep :8604 alive solely as the working v2-conformance demo referenced in outreach.

### ESTIMATED REVENUE IMPACT
Not directly additive — it is a course correction that stops further spend on a provably-zero-demand channel. Every hour invested in Sui-rail discoverability has an expected conversion of $0 given no buyer stack can settle sui:testnet. Redirecting the same effort to the Base rail targets the only observable paid-traffic pool in the ecosystem (Agent402 index: 82,536 paid tools, 1,320 distinct Base payees) and is a precondition for the RQ-019 anchor-payer strategy and any $20/day outcome. Spawns RQ-037 (why our indexed tools show price:null and whether that hides us from /api/find even on supported rails) and RQ-038 (whether ANY discovery surface routes real paid demand to Sui-settled tools, or Sui is credibility-only ecosystem-wide).

## 2026-08-22 — RQ-037: Why does Agent402's crawler show our routable tools with price:null, paywall:null and payToByNetwork:{} despite health=1 — and does a null-price tool get excluded from /api/find + /api/route?

### VERDICT
**Answered. Root cause found and it is a one-field fix on OUR side.** Three sub-answers from reading Agent402's shipped source (`MikeyPetrillo/Agent402`, `src/x402-live-quote.js` + `src/x402-index.js`) plus a live index pull:

1. **The quote-probe IS firing for us.** Live `/api/index?seller=da6d5c66044ea4.lhr.life` (19:12Z) shows all three SKUs now carry `networks:["sui:testnet"]` — `enrichLiveQuotes()` (index.js ~1517-1571) probed our GET routes, got our 402, and parsed the accepts array. The probe pipeline works end-to-end.
2. **Price stays null because our accepts entry has NO `extra` field.** `quoteFromAccepts()` prices an entry ONLY when decimals are known: either `extra.decimals` is an integer, or `isUsdc(entry)` matches `/^usdc|usd coin$/i` against `extra.name` (USDC_DECIMALS=6 hardcoded). Our 402 emits `{"scheme":"exact","network":"sui:testnet","amount":"15000","asset":"0xa1ec…::usdc::USDC","payTo":"0x8b35…"}` with **no `extra` object at all** → decimals unknown → Agent402 deliberately leaves price null ("an amount we cannot price … a wrong exponent is a 1000x pricing error"). This also explains the ecosystem-wide symptom documented in their own header comment (~1/3 of index rows priceless on 2026-08-07).
3. **`payToByNetwork:{}` is structural, not a defect.** That field is only ever populated by `bazaarItemToTool()` (CDP-Bazaar-sourced rows). For manifest-registered sellers like us, `enrichLiveQuotes()` applies ONLY price/networks/method and discards the learned payTo. Buyers are not affected: the router reads payTo live from the seller's actual 402 (`payToFromLive402`) before spending.
4. **Null price does NOT exclude us from find/route.** `payabilityOf()` returns "x402" when networks are present; router keeps unpriced rows. BUT the price tie-break maps unknown → Infinity: "unknown ranks last among equals." At equal match score we lose to every priced competitor, and buyer dashboards show priceUsd 0.

### EVIDENCE
- Source: https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/x402-live-quote.js (header comment documents this exact defect class; `quoteFromAccepts`/`isUsdc` pricing logic; `probeMethodsFor` GET→POST ladder)
- Source: https://raw.githubusercontent.com/MikeyPetrillo/Agent402/main/src/x402-index.js (`enrichLiveQuotes` candidate filter + application at ~1560-1568; `normaliseManifestTools` string-resources → price null at ~804-880; `parseManifestPrice` reads only OBJECT fields `price_usd|priceUsd|price|amount`; `payabilityOf` + `priceRank` at ~530-555; `routeQuery` pool construction at ~2776+)
- Live state: `https://agent402.tools/api/index?seller=da6d5c66044ea4.lhr.life` → health:1, routable:true, 3 SKUs with networks:["sui:testnet"], all price:null, payToByNetwork:{} (fetched 2026-08-22T19:12Z)
- Our live 402: `GET https://da6d5c66044ea4.lhr.life/v1/sentiment?text=probe` → 402 with base64 `payment-required` header AND JSON body accepts[], entry lacking `extra`
- Bonus defect observed in same index row: 4 junk tools listed (`/`, `/bazaar`, `/stats`, catch-all `/{path}` as "Paid") — OpenAPI-derived rows that dilute our listing and let the catch-all match buyer queries.

### RECOMMENDED ACTION (one directive for CEO)
Issue **DIR-033: add `"extra":{"name":"USDC","decimals":6}` to EVERY accepts entry emitted by both rails (:8604 sui_market_server.py and :8610 revenue_server.py), then re-verify within one crawl cycle that /api/index shows real prices on our rows.** Belt-and-braces: while editing, also convert the manifest to rich objects `{path,method:"GET",price:"$0.015",name,…}` per DIR-031 (parseManifestPrice reads those), restrict /openapi.json to the 5 paid SKUs (kills the 4 junk rows incl. the catch-all), and regression-test that the facilitator/x402scan still accept challenges containing `extra`. Expected observable success: `curl agent402.tools/api/index?seller=<origin>` shows `"price":0.015` etc. within ~2h.

### ESTIMATED REVENUE IMPACT
Small but compounding: priced rows stop losing every price tie-break in /api/route and read as a real $ product instead of priceUsd:0 noise. Does NOT by itself create demand (RQ-035/RQ-017 verdicts stand: Sui rail is credibility-only). Real value lands when repeated on the :8610 Base rail at its stable origin — there, being priced at $0.05/report vs "unknown" is the difference between winning and losing the tie-break against priced competitors in the only network with buyers. Effort: <1 hour builder work.
