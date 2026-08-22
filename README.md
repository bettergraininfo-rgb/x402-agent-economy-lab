# x402 Agent Economy Lab

[![integration](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/actions/workflows/ci.yml)

**Machine-payable NLP micro-services for autonomous AI agents.**

Your agent needs to score sentiment, extract entities, or summarize text —
thousands of times a day, without a human holding a credit card. This project
implements the full [x402](https://x402.org) payment protocol so an agent can
pay **per call** in stablecoin value, with no API keys, no accounts, no monthly
minimums.

## 🛒 Buy now — real USDC on Base mainnet

No signup. Pay in USDC, get your result as a GitHub comment, verified on-chain:

1. Send USDC on **Base mainnet** to `0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f`
2. [Open an issue using the x402 Order template](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/issues/new?template=x402-order.yml) — paste your tx hash + input text
3. Our fulfillment bot verifies your payment against the blockchain and posts your JSON result

| Service | Price / call |
|---|---|
| `/v1/sentiment` | **$0.015** |
| `/v1/entity-extract` | **$0.030** |
| `/v1/summarize` | **$0.075** |
| `/v1/report` (bundle: sentiment + summary + entities) | **$0.020** |
| `/v1/batch` (bulk sentiment over `|||`-separated docs) | **$0.050** |

### What happens after you pay

| Step | What occurs | How you can check it |
|---|---|---|
| 1. You send USDC | Your transfer lands on Base mainnet | Any Base explorer — your tx hash |
| 2. You open the order issue | Intake labels it `x402-order` | Issue appears instantly |
| 3. Fulfillment bot polls (~10 min) | It re-reads **the chain**, not your claim: recipient must match our wallet, amount ≥ list price, tx hash never seen before | Bot comments the verification result |
| 4. Verified → result posted | JSON output as an issue comment; order logged to the public ledger [`org/revenue_ledger.json`](org/revenue_ledger.json) | Ledger commit history |
| Invalid tx (wrong amount / replayed / not found) | Order is **rejected and closed** — no result, ledger untouched | Rejection comment cites the exact reason |

The verification logic is ~100 lines of readable Python ([`storefront.py`](storefront.py)) —
the bot trusts the blockchain, never the buyer's screenshot. Replay protection
means one payment buys exactly one call.

> 📖 **New here?** Read the [first machine-payment walkthrough](docs/tutorial-first-machine-payment.md) — a complete, honest tour of both purchase paths with real captured requests and responses.

## The catalog

| Endpoint | Price / call | Input | Output |
|---|---|---|---|
| `POST /v1/sentiment` | **$0.015** | `{"text": "..."}` | label + score |
| `POST /v1/entity-extract` | **$0.030** | `{"text": "..."}` | typed entities |
| `POST /v1/summarize` | **$0.075** | `{"text": "..."}` | summary |
| `POST /v1/report` | **$0.020** | `{"text": "..."}` | bundled sentiment + summary + entities |
| `POST /v1/batch` | **$0.050** | `{"text": "doc1 ||| doc2 ||| ..."}` | per-doc sentiment + label distribution |

At 10k calls/day that is $150/mo for sentiment — cheaper than any key-based
NLP API at equivalent volume, and settleable by a non-human wallet.

## How a purchase works (the x402 loop)

```text
Agent                                Server
  |  GET /v1/sentiment                  |
  |------------------------------------>|
  |  402 Payment Required               |   challenge: pay_to, amount, nonce
  |<------------------------------------|
  |  sign payment payload               |
  |  retry + X-PAYMENT header           |
  |------------------------------------>|
  |                                     |   verify signature, amount,
  |                                     |   replay window, nonce
  |  200 + result + receipt             |
  |<------------------------------------|
```

Every failure mode an attacker would try is tested and rejected: replayed
payments, tampered amounts, underpayment, stale nonces (`test_security.py`).

## Run your own instance in 60 seconds

```bash
git clone https://github.com/bettergraininfo-rgb/x402-agent-economy-lab.git
cd x402-agent-economy-lab && bash setup.sh

# paid API with all three endpoints + dynamic repricing
.venv/bin/uvicorn market_server:app --port 8503 &
.venv/bin/python agent_client.py        # watch an agent discover, pay, consume
```

Point any x402-compatible HTTP client at `http://localhost:8503`. The bazaar
endpoint (`GET /bazaar`) exposes machine-readable pricing so buyer agents can
discover services autonomously.

## What is proven vs. in progress

**Proven end-to-end (tested, reproducible):**
- Full x402 flow: 402 challenge → signed payment → verify → serve → receipt
- Real **on-chain settlement**: every purchase is an actual signed transaction,
  verified against chain state before service is served — proven on Sui devnet
  (txns `FJpQrgYm…`, `2HxocRYh…`), including an agent-deployed Move escrow
  contract (create/release/cancel)
- Agent-to-agent commerce: two independent nodes discovering and paying each
  other, ledger balanced to the cent
- Dynamic pricing: prices adapt to demand shocks within [0.4x, 3x]
- **Storefront order lifecycle, both branches tested live**: a fake tx hash
  was rejected by on-chain verification, its issue auto-closed, ledger
  untouched — and verified payments post results + ledger entries
- Spec-conformant x402 challenges: our Sui rail emits v2-shaped `402`s
  (base64 `payment-required` envelope, `accepts[]` with the `exact` scheme),
  readable by standard x402 clients

**In progress (honest status):**
- Hosted public endpoint — the servers above run anywhere; we are standing up
  a permanent URL. Open an
  [issue](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/issues)
  if you want access the day it lands.
- Base mainnet facilitator wiring — `production_cdp.py` contains the complete
  CDP/x402 SDK integration path, gated only on credentials.

## Who this is for

- **Agent framework builders** — give your agents a wallet and they can buy
  NLP capability mid-task with zero human approval loops.
- **x402 ecosystem projects** — a reference implementation of seller-side
  verification, dynamic pricing, A2A settlement, and on-chain receipts you can
  lift directly.
- **Researchers** — a runnable micro-economy: buyer swarms with budget
  guardrails, demand shocks, price elasticity, all observable.

## MCP-ready

Any Model Context Protocol host (Claude Code, Cursor, …) can connect
`mcp_bazaar_server.py` and purchase bazaar services as native tools.

## Repository map

| Stage | File | What it proves |
|---|---|---|
| 1. Single paid API | `server.py` + `agent_client.py` | Complete x402 flow |
| 1a. Security | `test_security.py` | Replay/tamper/underpay rejection |
| 2. Multi-service bazaar | `bazaar.py` + `economy.py` | Discovery + buyer swarm |
| 3. Dynamic pricing | `market_server.py` + `market_sim.py` | Demand-adaptive prices |
| 4. Live-data services | `chainfeed.py` | Agents buy real Base block data |
| 5. Production path | `production_cdp.py` | CDP/x402 SDK wiring |
| 6. A2A commerce | `a2a_economy.py` | Node-to-node balanced trade |
| 7. On-chain settlement | `sui_market_server.py` + Move sources | Chain-verified payments + escrow |

## Going to production

1. Create free keys at https://portal.cdp.coinbase.com
2. `export CDP_API_KEY_ID=... CDP_API_KEY_SECRET=... CDP_WALLET_SECRET=...`
3. Fund a Base Sepolia wallet with faucet USDC
   (`0x036CbD53842c5426634e7929541eC2318f3dCF7e`)
4. Swap `MockFacilitator.settle()` for
   `x402ResourceServerSync.verify_payment()/settle_payment()` — see
   `production_cdp.py`.

---

Rails are not demand — this lab proves agents *can* transact autonomously;
earning money still requires selling something people actually want. That is
the experiment running now.
