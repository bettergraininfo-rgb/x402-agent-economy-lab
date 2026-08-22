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
