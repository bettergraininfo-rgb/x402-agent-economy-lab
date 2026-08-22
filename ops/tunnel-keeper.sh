#!/usr/bin/env bash
# ops/tunnel-keeper.sh — keep a public localhost.run tunnel to sui_market_server :8604
# alive and keep the Agent402 index registration in sync with the current subdomain.
# Anonymous lhr.life subdomains are random per connection; on any reconnect we
# re-POST /api/index/register so the index follows the new origin.
set -u
LOG=/tmp/tunnel-keeper.log
URLFILE=/tmp/tunnel-current-url
SSHLOG=/tmp/tunnel-8604.log
INDEX_URL="https://agent402.tools/api/index/register"
PUBURL_FILE="$(cd "$(dirname "$0")/.." && pwd)/docs/PUBLIC_URL.txt"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

start_tunnel() {
  : > "$SSHLOG"
  nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes \
        -R 80:localhost:8604 nokey@localhost.run > "$SSHLOG" 2>&1 &
  local pid=$!
  for _ in $(seq 1 20); do
    sleep 3
    url=$(grep -oE 'https://[a-z0-9]+\.lhr\.life' "$SSHLOG" | head -1)
    if [ -n "$url" ]; then
      echo "$url" > "$URLFILE"
      # DIR-025 lockstep: every rotation overwrites the public URL file.
      { echo "$url"; echo; echo "updated: $(date '+%F %T') by tunnel-keeper (auto-rotation)"; } > "$PUBURL_FILE"
      log "tunnel up: $url (pid $pid); PUBLIC_URL.txt updated"
      return 0
    fi
    kill -0 "$pid" 2>/dev/null || break
  done
  log "ERROR: tunnel failed to come up"
  return 1
}

register() {
  local url="$1"
  resp=$(curl -s --max-time 30 -X POST "$INDEX_URL" -H 'content-type: application/json' \
         -d "{\"origin\":\"$url\"}")
  log "register $url -> $resp"
  case "$resp" in
    *'"listed":true'*) echo "$url" > /tmp/registered-origin-ok; return 0 ;;
    *) log "register NOT confirmed (will retry next cycle): $resp"; return 1 ;;
  esac
}

healthy() {
  local url="$1"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url/.well-known/x402")
  [ "$code" = "200" ]
}

log "keeper started"
while true; do
  url=$(cat "$URLFILE" 2>/dev/null || true)
  ok=$(cat /tmp/registered-origin-ok 2>/dev/null || true)
  if [ -n "$url" ] && [ "$url" != "$ok" ]; then
    # Origin changed or previous registration unconfirmed: (re-)register with backoff.
    # Rate limit is 5 submissions/hour/IP — a rejected POST may still count, so wait
    # 10 min between attempts instead of hammering every cycle.
    if [ -f /tmp/tunnel-register-last ] && [ $(( $(date +%s) - $(cat /tmp/tunnel-register-last) )) -lt 600 ]; then
      :
    else
      date +%s > /tmp/tunnel-register-last
      register "$url" || true
    fi
  fi
  if [ -z "$url" ] || ! healthy "$url"; then
    log "tunnel unhealthy or missing (was: ${url:-none}); restarting"
    pkill -f 'ssh .*80:localhost:8604' 2>/dev/null
    rm -f /tmp/registered-origin-ok
    sleep 2
    start_tunnel || { sleep 60; continue; }
    url=$(cat "$URLFILE")
    register "$url" || true
  fi
  sleep 60
done
