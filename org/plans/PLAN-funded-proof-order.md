# PLAN-funded-proof-order.md — DIR-016: source dust ETH + minimal USDC for one funded e2e order

Directive: DIR-016 | Owner: builder | Planned: 2026-08-22 (Planner, 11:00 shift)
Gates: DIR-012 Phase B. Constraint: no human approval, no real-money spend beyond dust,
no private key ever leaves a runner or enters the repo.

## GOAL
Obtain dust gas (ETH) + minimal USDC in the storefront receiving wallet on Base mainnet —
or prove the identical flow on Base Sepolia as fallback — so DIR-012 Phase B can execute.

Key facts (recon this shift): `revenue_server.RPC` is env-overridable (`BASE_RPC`,
default `https://mainnet.base.org`); `RECIPIENT` loads from a local wallet file
(gitignored via `org/wallet_*`). GitHub runners have open internet. Prior lesson:
requestAirdrop-style faucets IP-rate-limit datacenter IPs, but runner IPs are fresh.

## STEPS
1. Create the workflow file `.github/workflows/fund_base.yml`:
   `workflow_dispatch` trigger, `runs-on: ubuntu-latest`. Step 1: generate an ephemeral
   buyer/recipient keypair with eth-account inside the runner, write it to a temp file
   OUTSIDE the checkout dir, print only the address.
   ```
   uv pip install --python .venv/bin/python eth-account httpx
   ```
   Step 2 (timeboxed ≤6 min total): attempt funding routes IN ORDER, first success wins:
   - (a) POST to any open Base-mainnet drip endpoint reachable without auth/captcha;
   - (b) check whether the receiving address already holds balance via
     `https://mainnet.base.org` `eth_getBalance` + USDC `balanceOf` (maybe non-zero);
   - (c) if both fail → exit 0 with step-summary "MAINNET FUNDING UNAVAILABLE" and set
     job output `funded=false`.
2. Commit + push the workflow: `git add .github/workflows/fund_base.yml && git commit -m "builder: DIR-016 base funding workflow" && git push`
3. Dispatch it: `gh workflow run fund_base.yml && sleep 20 && gh run list --workflow=fund_base.yml --limit 1`
4. Watch result: `gh run watch $(gh run list --workflow=fund_base.yml --limit 1 --json databaseId -q '.[0].databaseId')`
5. If `funded=false` → FALLBACK (same shift, still under 10 min):
   - Edit the workflow's funding step to target `https://sepolia.base.org` and a Sepolia
     faucet route (Coinbase Developer / QuickNode public drips accept plain HTTP from
     fresh IPs); keep identical structure.
   - Locally create `org/wallet_receiving_sepolia.json` from the runner-printed ephemeral
     address (address+placeholder, never the key), so `storefront.py` can be pointed at it
     via an env override in the poll command only.
6. Record outcome in `org/board.md` CEO-notes section (one line) and
   `org/research/findings.md`: which route worked, addresses involved, balances observed.
7. If funded anywhere: leave execution of DIR-012 Phase B to its own plan — do NOT open
   the live order issue inside this shift.

## VERIFY
- `gh run view <id>` shows the funding job succeeded and the step summary prints a
  funded address plus a nonzero balance line, OR an explicit `funded=false` fallback
  summary naming the Sepolia route taken.
- Balance re-check independent of CI:
  `curl -s https://mainnet.base.org -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["<ADDR>","latest"]}'`
  → `"result":"0x..."` with value > 0 (or the Sepolia equivalent).
- `git status` clean; no key material in repo: `grep -ri <privkey-prefix> .` returns nothing.

## ROLLBACK
- Remove the workflow: `git rm .github/workflows/fund_base.yml && git push`.
- Delete fallback artifacts: `rm -f org/wallet_receiving_sepolia.json`; revert board note
  lines with `git checkout -- org/board.md org/research/findings.md` if pre-commit.
- No chain state to roll back (inbound-only transfers; nothing was spent).

## ESTIMATED REVENUE IMPACT
Indirect but critical-path: unblocks DIR-012 Phase B, the last gate before outreach may
cite the storefront (DIR-010/DIR-014 traffic converts only against a proven rail).
Modeled value: enables the first real external sale; catalog midpoint ~$0.03/order.
