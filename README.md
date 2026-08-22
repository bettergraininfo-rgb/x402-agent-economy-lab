# x402 Agent Economy Lab

A working laboratory for the **x402 agent-payment protocol** (https://x402.org):
AI agents that discover services, negotiate prices, pay per request, and run
an autonomous micro-economy — with live on-chain data as the product.

Built and verified end-to-end. Settlement is simulated (`payment_core.MockFacilitator`);
every protocol behavior (402 challenge, signed retries, replay/tamper rejection,
budget guardrails, dynamic pricing, A2A commerce) is real and tested.

## The progression

| Stage | File | What it proves |
|---|---|---|
| 1. Single paid API | `server.py` + `agent_client.py` | Full x402 flow: 402 → sign → retry → settle → serve |
| 1a. Security | `test_security.py` | Replayed, tampered, underpaid requests all rejected |
| 2. Multi-service bazaar | `bazaar.py` + `economy.py` | Discovery endpoint; 3 buyer agents with distinct budgets/preferences |
| 3. Dynamic pricing | `market_server.py` + `market_sim.py` | Prices adapt to demand shocks (0.4x–3x of base) |
| 4. Live-data services | `chainfeed.py` + `chainfeed_client.py` | Agents buy REAL Base mainnet block data via the payment loop |
| 5. Production path | `production_cdp.py` | Real CDP/x402 SDK wiring, gated until credentials exist |
| 6. Agent-to-agent commerce | `a2a_economy.py` | Two independent nodes discovering & paying each other, balanced ledger |

## Quick start

```bash
bash setup.sh
cd ~/x402-agent-service

# single-service flow
.venv/bin/uvicorn server:app --port 8402 &
.venv/bin/python agent_client.py
.venv/bin/python test_security.py

# dynamic market + demand shock
.venv/bin/uvicorn market_server:app --port 8503 &
.venv/bin/python market_sim.py

# live Base-mainnet data marketplace (needs outbound RPC access)
.venv/bin/uvicorn chainfeed:app --port 8504 &
.venv/bin/python chainfeed_client.py

# two-node A2A economy
.venv/bin/python a2a_economy.py
```

## Key design points

- **Payment core** (`payment_core.py`): HMAC-signed payloads, per-request nonce,
  replay window, amount enforcement — mirrors what a real facilitator verifies.
- **Budget guardrails**: every buyer enforces a hard cap; refusals are logged.
- **Dynamic pricing**: conversion-rate-driven repricing bounded to [0.4x, 3x].
- **A2A ledger check**: `total earned == total spent` asserted at end of run.

## Going to production

1. Create free keys at https://portal.cdp.coinbase.com
2. `export CDP_API_KEY_ID=... CDP_API_KEY_SECRET=... CDP_WALLET_SECRET=...`
3. Fund a Base Sepolia wallet with faucet USDC
   (`0x036CbD53842c5426634e7929541eC2318f3dCF7e`)
4. Replace `MockFacilitator.settle()` calls with the real
   `x402ResourceServerSync.verify_payment()/settle_payment()` — see
   `production_cdp.py`.

The honest economics note stands: rails ≠ demand. This lab proves agents
*can* transact autonomously; earning money still requires selling something
people actually want.

## Daily autonomous operation

`daily_run.py` + the Hermes cron job `x402-agent-economy-daily` boot a fresh
market each morning, run the buyer swarm through baseline + demand-shock
phases, and post stats to chat.
