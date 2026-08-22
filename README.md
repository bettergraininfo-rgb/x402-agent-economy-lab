# x402 Agent Economy Lab

[![integration](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/actions/workflows/ci.yml)

**Machine-payable NLP micro-services for autonomous AI agents.**

Your agent needs to score sentiment, extract entities, or summarize text —
thousands of times a day, without a human holding a credit card. This project
implements the full [x402](https://x402.org) payment protocol so an agent can
pay **per call** in stablecoin value, with no API keys, no accounts, no monthly
minimums.

## The catalog

| Endpoint | Price / call | Input | Output |
|---|---|---|---|
| `POST /v1/sentiment` | **$0.001** | `{"text": "..."}` | label + score |
| `POST /v1/entity-extract` | **$0.002** | `{"text": "..."}` | typed entities |
| `POST /v1/summarize` | **$0.005** | `{"text": "..."}` | summary |

At 10k calls/day that is $50/mo for sentiment — cheaper than any key-based
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
