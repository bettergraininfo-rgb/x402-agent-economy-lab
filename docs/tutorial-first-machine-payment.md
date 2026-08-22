# Tutorial: your first machine-payable API call

A working walkthrough of buying AI micro-services with **no API keys, no accounts, no
sign-ups** — you pay per call in USDC and get results back. Everything below was
captured from the live code in this repository, not mocked up.

## What you can buy

| Service | What it does | Price (USDC, Base mainnet) |
|---|---|---|
| `/v1/sentiment` | Label + score for any text | 0.015 |
| `/v1/entity-extract` | Organizations & proper nouns | 0.030 |
| `/v1/summarize` | Extractive summary | 0.075 |
| `/v1/analyze` | Bundle: summary + sentiment + entities | 0.250 |

Two purchase paths exist today:

- **Path A — GitHub-issue storefront** (works for anyone, right now)
- **Path B — run the server yourself and pay over HTTP** (for agent developers)

---

## Path A: buy through the GitHub issue storefront

This machine has no inbound network, so the storefront lives where the customers are:
GitHub issues. The flow is deliberately simple.

1. **Pay on-chain.** Send the exact USDC amount for your chosen service on **Base
   mainnet** to `0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f`.
2. **Open an issue** using the **x402 Order** template
   ([open one here](https://github.com/bettergraininfo-rgb/x402-agent-economy-lab/issues/new?template=x402-order.yml)).
   Fill in: the endpoint, your transaction hash (`0x…`), and the input text.
3. **Get your result.** The fulfillment bot verifies your payment **on-chain** — it scans
   the Base chain for a real USDC `Transfer` event to the receiving address for the
   correct amount, with a replay guard so the same tx hash can never be reused — then
   posts the JSON result as a comment and closes the issue.

Example of a filled order body:

```text
Service (endpoint): /v1/entity-extract
Transaction hash:   0xabc123…(your real Base tx hash)
Input text:         Coinbase shipped the x402 Bazaar on Base in Boston last Tuesday.
```

What you'd get back (genuine output from the shipped entity extractor):

```json
{
  "organizations": ["Base", "Coinbase"],
  "proper_nouns": ["Bazaar", "Boston", "Tuesday"]
}
```

**Honest status:** payment verification is live and adversarially tested — fabricated or
already-used transaction hashes are rejected on-chain before anything is served. Results
are delivered by a fulfillment bot polling on a roughly 10-minute loop. There is no
public HTTPS endpoint yet; if you need low-latency programmatic access instead of the
issue flow, open an issue and say so — that demand signal directly prioritizes hosting.

Other genuine sample outputs from this exact codebase:

```json
// /v1/sentiment → "The x402 protocol makes HTTP APIs machine-payable. …"
{"label": "neutral", "score": 0.0}

// /v1/summarize → 3-sentence input about x402 settlement
{"summary": "Agents settle in USDC per call, no accounts or API keys required",
 "original_sentences": 3}
```

---

## Path B: run it yourself and pay over HTTP

The same catalog is served by `sui_market_server.py` (Sui rail). Clone the repo and run:

```bash
python3 sui_market_server.py          # listens on 127.0.0.1:8604
```

Ask for a service without paying, and the server answers with a machine-readable **402
Payment Required challenge** — this is the core x402 idea. Captured live:

```json
{
  "error": "Payment Required",
  "scheme": "sui-transfer",
  "pay_to": "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a",
  "amount_mist": 50000000,
  "network": "sui-devnet",
  "instructions": "Execute a SUI transfer of amount_mist to pay_to, then retry with header X-SUI-TX-DIGEST: <digest>"
}
```

A buyer agent executes that transfer, then retries with proof:

```bash
curl -H "X-SUI-TX-DIGEST: <your-tx-digest>" \
     "http://127.0.0.1:8604/v1/sentiment?text=hello"
```

The server verifies the digest **on-chain** (real settlement, correct recipient and
amount) before serving. Settlements are visible on Sui Explorer — e.g. our own test
settlements `FJpQrgYm…` and `2HxocRYh…` on devnet.

Minimal buyer loop in Python:

```python
import requests

BASE = "http://127.0.0.1:8604"
r = requests.get(f"{BASE}/v1/sentiment", params={"text": "agents gonna agent"})

if r.status_code == 402:
    challenge = r.json()                      # pay_to, amount_mist, network
    digest = sui_transfer(challenge)          # your wallet signs & broadcasts
    r = requests.get(f"{BASE}/v1/sentiment",
                     params={"text": "agents gonna agent"},
                     headers={"X-SUI-TX-DIGEST": digest})

print(r.json())
```

---

## Building your own machine-payable API

Three patterns from this repo worth stealing:

1. **Price-gate with a 402 challenge**, not auth. The response body *is* the invoice:
   recipient, exact amount, network, and how to present proof. Any HTTP client can
   comply without an SDK.
2. **Verify on-chain before serving. Never trust the header.** Look up the claimed
   transaction on the chain itself and check recipient + amount. See
   `verify_payment()` in `revenue_server.py`.
3. **Replay-guard every proof.** A tx hash is single-use; record spent digests/hashes
   or buyers will serve themselves forever with one payment. See `_load_ledger()` /
   `_record()`.

Where to look: `sui_market_server.py` (HTTP + 402 flow), `revenue_server.py`
(Base-mainnet USDC verification), `storefront.py` (GitHub-as-storefront),
`.github/ISSUE_TEMPLATE/x402-order.yml` (the order form).

---

Questions, custom volumes, or want a different NLP task priced? Open an issue — a human
(or very determined bot) will answer.
