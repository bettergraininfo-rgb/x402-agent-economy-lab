#!/usr/bin/env bash
# listing_sync.sh — DIR-027 Step C: independent @15min watcher keeping the Agent402
# registration in lockstep with tunnel URL rotations. Delegates the actual POST to
# org/state/register_gate.sh (single-attempt, quota-aware policy). DRY_RUN=1 logs the
# intended action without POSTing. Exits 0 silently when in-sync or gated.
set -u

ROOT="/home/jackie/x402-agent-service"
GATE="$ROOT/org/state/register_gate.sh"
PUB="$ROOT/docs/PUBLIC_URL.txt"
ORIGIN_FILE="$ROOT/org/state/registered_origin.txt"
SALES="$ROOT/org/sales_log.md"

URL="$(head -1 "$PUB" 2>/dev/null | tr -d '[:space:]')"
[ -z "$URL" ] && exit 0
REG="$(head -1 "$ORIGIN_FILE" 2>/dev/null | tr -d '[:space:]')"
if [ "$URL" = "$REG" ]; then
  exit 0
fi

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "| $(date -u +%FT%TZ) | DIR-027 listing-sync DRY_RUN | would POST /api/index/register origin=$URL (no POST performed) |" >> "$SALES"
  exit 0
fi

bash "$GATE"
exit 0
