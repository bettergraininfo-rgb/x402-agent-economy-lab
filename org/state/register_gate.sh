#!/usr/bin/env bash
# register_gate.sh — DIR-027 Step B: quota-disciplined single-attempt Agent402 registration.
# Policy (plan V3): refuse to POST if
#   (a) the prior attempt got a rate-limit body less than 55 min ago, OR
#   (b) head -1 docs/PUBLIC_URL.txt equals org/state/registered_origin.txt (in-sync).
# Otherwise perform exactly ONE POST to /api/index/register, append timestamp + VERBATIM
# response to org/sales_log.md, record attempt class to org/state/last_register_attempt.txt,
# update org/state/registered_origin.txt ONLY on "listed":true, echo one line to
# org/system_events.log. Read-only except those five files. Never touches wallet files.
set -u

ROOT="/home/jackie/x402-agent-service"
STATE_DIR="$ROOT/org/state"
PUB="$ROOT/docs/PUBLIC_URL.txt"
ORIGIN_FILE="$STATE_DIR/registered_origin.txt"
ATTEMPT_FILE="$STATE_DIR/last_register_attempt.txt"
SALES="$ROOT/org/sales_log.md"
EVENTS="$ROOT/org/system_events.log"

URL="$(head -1 "$PUB" 2>/dev/null | tr -d '[:space:]')"
[ -z "$URL" ] && exit 0
mkdir -p "$STATE_DIR"

REG="$(head -1 "$ORIGIN_FILE" 2>/dev/null | tr -d '[:space:]')"
if [ "$URL" = "$REG" ]; then
  exit 0
fi

NOW="$(date +%s)"
if [ -f "$ATTEMPT_FILE" ]; then
  TS="$(head -1 "$ATTEMPT_FILE" | awk '{print $1}')"
  CLS="$(head -1 "$ATTEMPT_FILE" | awk '{print $2}')"
  if [ "${CLS:-}" = "rate-limited" ] && [ -n "${TS:-}" ] && [ $(( NOW - TS )) -lt 3300 ]; then
    exit 0
  fi
fi

STAMP="$(date -u +%FT%TZ)"
RESP="$(curl -s --max-time 20 -X POST https://agent402.tools/api/index/register \
  -H 'content-type: application/json' \
  -d "{\"origin\":\"$URL\"}")"

CLS="error"
if printf '%s' "$RESP" | grep -q '"listed"[[:space:]]*:[[:space:]]*true'; then
  CLS="ok"
elif printf '%s' "$RESP" | grep -qi 'rate limit'; then
  CLS="rate-limited"
fi
echo "$NOW $CLS" >> "$ATTEMPT_FILE"

{
  echo ""
  echo "| $STAMP | DIR-027 register-gate | POST /api/index/register origin=$URL | VERBATIM RESPONSE: $RESP |"
} >> "$SALES"

if [ "$CLS" = "ok" ]; then
  printf '%s\n' "$URL" > "$ORIGIN_FILE"
  echo "$STAMP | LISTING-SYNC | re-registered $URL with Agent402 (listed:true)" >> "$EVENTS"
else
  echo "$STAMP | LISTING-SYNC | registration NOT confirmed for $URL (class=$CLS; gated retry): $RESP" >> "$EVENTS"
fi
exit 0
