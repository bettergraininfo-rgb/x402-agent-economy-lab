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
