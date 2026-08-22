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
| `/v1/report` | Bundle: sentiment + summary + entities | 0.020 |
| `/v1/batch` | Bulk sentiment over `|||`-separated docs | 0.050 |

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
are delivered by a fulfillment bot polling on a roughly 10-minute loop. A public HTTPS
instance of the Sui rail also exists (see Path B) but rides a rotating tunnel kept alive
by an auto-reconnect keeper, so treat the GitHub issue flow as the stable path. If you
need low-latency programmatic access on Base instead of the issue flow, open an issue
and say so — that demand signal directly prioritizes hosting.

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
Payment Required challenge** — this is the core x402 idea. Captured live from the public
instance (x402 v2 exact scheme, sui:testnet USDC, August 22, 2026):

```json
{
  "x402Version": 2,
  "accepts": [{
    "scheme": "exact",
    "network": "sui:testnet",
    "amount": "15000",
    "asset": "0xa1ec7fc00a6f40db9693ad1415d0c193ad3906494428cf252621037bd7117e29::usdc::USDC",
    "payTo": "0x8b3553395bdf688c89431c1cdf03bd9f7f555eb0fe0118d395a37270e78c924a",
    "maxTimeoutSeconds": 600
  }],
  "error": "Payment Required"
}
```

(The challenge also arrives base64-encoded in the spec-standard `payment-required`
response header; the body above is its decoded content. Legacy-dialect fields are still
present in the body for older buyers.)

A buyer agent executes the transfer described by `accepts`, then retries with proof in
the `PAYMENT-SIGNATURE` header (standard x402 client libraries do this automatically):

```bash
curl -H "PAYMENT-SIGNATURE: <signed-payment>" \
     "https://<current-public-host>/v1/sentiment?text=hello"
```

The server verifies the payment **on-chain** (real settlement, correct recipient and
amount) before serving. Settlements are visible on Sui Explorer — e.g. our own test
settlements `FJpQrgYm…` and `2HxocRYh…`.

The public origin rotates when the tunnel reconnects; the authoritative current URL is
kept in [`docs/PUBLIC_URL.txt`](PUBLIC_URL.txt), and the service is registered with the
[Agent402](https://agent402.tools) discovery index, which re-checks health hourly.

Minimal buyer loop in Python:

```python
import requests

BASE = "http://127.0.0.1:8604"   # or the current public origin (docs/PUBLIC_URL.txt)
r = requests.get(f"{BASE}/v1/sentiment", params={"text": "agents gonna agent"})

if r.status_code == 402:
    challenge = r.json()                       # accepts[]: payTo, amount, network
    sig = sign_and_pay(challenge)              # your wallet signs & broadcasts
    r = requests.get(f"{BASE}/v1/sentiment",
                     params={"text": "agents gonna agent"},
                     headers={"PAYMENT-SIGNATURE": sig})

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
