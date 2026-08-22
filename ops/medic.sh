#!/usr/bin/env bash
# ops/medic.sh — self-healing restarts for the agent-economy services.
# Restarts anything down using known-good commands, logs every action to
# org/system_events.log so the whole company can see infrastructure history.
set -u
ROOT="$HOME/x402-agent-service"
PY="$ROOT/.venv/bin/python"
LOG="$ROOT/org/system_events.log"
cd "$ROOT" || exit 1

log() { echo "$(date -u +%FT%TZ) | MEDIC | $1" >> "$LOG"; }

restart() {
  local name="$1" port="$2" target="$3" probe="$4"
  # re-check before acting (avoid racing a service that just came up)
  curl -sf -m 5 -o /dev/null "$probe" && return 0
  log "restarting $name on :$port"
  pkill -f "uvicorn .*--port $port" 2>/dev/null; sleep 1
  nohup "$PY" -m uvicorn "$target" --host 127.0.0.1 --port "$port" \
    >> "/tmp/agent-econ-$port.log" 2>&1 &
  sleep 6
  if curl -sf -m 8 -o /dev/null "$probe"; then
    log "$name RECOVERED on :$port (pid $!)"
    echo "MEDIC: restarted $name on :$port — verified healthy."
  else
    log "$name STILL DOWN after restart attempt (:${port})"
    echo "MEDIC FAILED: $name still down on :$port after restart — manual attention needed."
  fi
}

actions=0
out="$(restart "market-server" 8604 "sui_market_server:app" "http://127.0.0.1:8604/health")" && : 
[ -n "$out" ] && { echo "$out"; actions=1; }
out="$(restart "dashboard"    8605 "dashboard_api:app"   "http://127.0.0.1:8605/api/overview")"
[ -n "$out" ] && { echo "$out"; actions=1; }
out="$(restart "revenue-server" 8610 "revenue_server:app" "http://127.0.0.1:8610/health")"
[ -n "$out" ] && { echo "$out"; actions=1; }

[ $actions -eq 0 ] && exit 0
exit 0
