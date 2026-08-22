#!/bin/bash
# Full integration suite: boots every marketplace node, runs all flows.
# Exits non-zero on any failure. Used locally and by GitHub Actions.
set -e
cd "$(dirname "$0")"

# Clear any stale servers from previous runs/dev sessions
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "uvicorn bazaar:app" 2>/dev/null || true
pkill -f "uvicorn market_server:app" 2>/dev/null || true
pkill -f "uvicorn chainfeed:app" 2>/dev/null || true
sleep 1

PY=".venv/bin/python"
UVICORN=".venv/bin/uvicorn"

echo "=== [1/6] unit: payment core security ==="
$UVICORN server:app --port 8402 >/dev/null 2>&1 &
S0=$!
sleep 2
$PY test_security.py
kill $S0

echo "=== [2/6] single-service flow ==="
$UVICORN server:app --port 8402 >/dev/null 2>&1 &
S1=$!
sleep 2
$PY agent_client.py
kill $S1

echo "=== [3/6] bazaar + buyer economy ==="
$UVICORN bazaar:app --port 8502 >/dev/null 2>&1 &
S2=$!
sleep 2
$PY economy.py
kill $S2

echo "=== [4/6] dynamic pricing under demand shock ==="
$UVICORN market_server:app --port 8503 >/dev/null 2>&1 &
S3=$!
sleep 2
$PY market_sim.py
kill $S3

echo "=== [5/6] ChainFeed: live Base mainnet data ==="
$UVICORN chainfeed:app --port 8504 >/dev/null 2>&1 &
S4=$!
sleep 2
$PY chainfeed_client.py
kill $S4

echo "=== [6/7] A2A economy with balanced ledger ==="
$PY a2a_economy.py

echo "=== [7/7] MCP server: agents buying via Model Context Protocol ==="
$PY mcp_bazaar_client_test.py

echo ""
echo "ALL INTEGRATION STAGES PASSED"
