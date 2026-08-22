#!/usr/bin/env bash
# ops/watchdog.sh — silent-when-healthy fleet health check.
# Exit 0 + empty stdout = all good (watchdog pattern: silence means healthy).
# Any output = something needs attention (delivered verbatim by cron).
set -u
ROOT="$HOME/x402-agent-service"
cd "$ROOT" || { echo "FATAL: cannot cd $ROOT"; exit 1; }

issues=""

# 1. Service liveness (HTTP, real request not just port open)
check_http() {
  local name="$1" url="$2"
  if ! curl -sf -m 8 -o /dev/null "$url"; then
    issues+="DOWN: $name ($url) not answering"$'\n'
  fi
}
check_http "market-server :8604" "http://127.0.0.1:8604/health"
check_http "dashboard    :8605" "http://127.0.0.1:8605/api/overview"
check_http "revenue-server:8610" "http://127.0.0.1:8610/health"

# 2. Revenue server must still point at the REAL wallet (catch config drift)
addr="$(curl -sf -m 8 http://127.0.0.1:8610/health | grep -o '0x[0-9a-fA-F]\{40\}' | head -1)"
if [ "$addr" != "0xFe3B1ca1E93d620876ca873a169C02614e6Ba39f" ]; then
  issues+="CONFIG DRIFT: revenue /health recipient is '$addr' (expected 0xFe3B…a39f)"$'\n'
fi

# 3. Repo integrity (persistence-aware: bots legitimately leave the repo dirty
#    mid-build; alert only when the dirty set is unchanged for >25 minutes)
dirty_list="$(git status --porcelain 2>/dev/null | sort)"
if [ -n "$dirty_list" ]; then
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    issues+="REPO BROKEN: git rev-parse failed"$'\n'
  fi
  dirty_hash="$(printf '%s' "$dirty_list" | shasum | cut -d' ' -f1)"
  dirty_n="$(printf '%s\n' "$dirty_list" | wc -l)"
  now=$(date +%s)
  state_file=/tmp/wd_dirty_state
  read -r p_hash p_n p_ts < "$state_file" 2>/dev/null || p_hash=""
  if [ "$p_hash" = "$dirty_hash" ]; then
    age=$(( now - p_ts ))
    [ $age -gt 1500 ] && issues+="REPO DIRTY: $dirty_n uncommitted change(s) untouched for $((age/60)) min (abandoned build?)"$'\n'
  else
    p_ts=$now
  fi
  echo "$dirty_hash $dirty_n $p_ts" > "$state_file"
fi
ahead="$(git rev-list --count origin/master..master 2>/dev/null)"
case "$ahead" in
  '') issues+="GIT REMOTE: cannot compare with origin/master (push broken?)"$'\n';;
  0) : ;;
  *) issues+="UNPUSHED: $ahead local commit(s) ahead of origin/master"$'\n';;
esac

# 4. Critical files exist
for f in org/kpis.json org/directives.json org/board.md org/revenue_ledger.json \
         revenue_server.py storefront.py .github/ISSUE_TEMPLATE/x402-order.yml; do
  [ -e "$ROOT/$f" ] || issues+="MISSING FILE: $f"$'\n'
done

# 5. Revenue ledger sanity (parseable JSON)
ledger_err="$(python3 - <<'EOF'
import json
try:
    d = json.load(open("org/revenue_ledger.json"))
    assert isinstance(d.get("lifetime_usdc"), (int, float))
except Exception as e:
    print(f"LEDGER CORRUPT: {e}")
EOF
)"
[ -n "$ledger_err" ] && issues+="$ledger_err"$'\n'

# 6. Cron fleet visible via hermes CLI (bots can still be listed = scheduler alive)
if ! hermes cron list >/tmp/wd_cron.out 2>&1; then
  issues+="SCHEDULER: hermes cron list FAILED"$'\n'
else
  sed -i 's/\x1b\[[0-9;]*m//g' /tmp/wd_cron.out   # strip ANSI colors
  active="$(grep -c '\[active\]' /tmp/wd_cron.out)"
  paused="$(grep -ciE '\[(paused|disabled)\]' /tmp/wd_cron.out)"
  # single transient agent failures self-heal next tick; alert only if persistent
  fails="$(grep -c '^    Execution: failed' /tmp/wd_cron.out)"
  errlines="$(grep '^    Execution: failed' /tmp/wd_cron.out | head -3)"
  [ "${fails:-0}" -ge 2 ] && issues+="CRON FAILURES: $fails jobs show failed executions:"$'\n'"$errlines"$'\n'
  if [ "${active:-0}" -lt 7 ]; then
    issues+="CRON FLEET: only $active active jobs (expected >= 7)"$'\n'
  fi
  if [ "${paused:-0}" -gt 0 ]; then
    issues+="CRON FLEET: $paused job(s) show paused/disabled:"$'\n'"$(grep -iE '\[(paused|disabled)\]' /tmp/wd_cron.out | head -3)"$'\n'
  fi
fi
rm -f /tmp/wd_cron.out

# 7. Stale business state (CEO/planner should be writing every ~15 min)
now=$(date +%s)
for f in org/directives.json org/kpis.json; do
  if [ -f "$ROOT/$f" ]; then
    age=$(( now - $(stat -c %Y "$ROOT/$f") ))
    if [ $age -gt 3600 ]; then
      issues+="STALE STATE: $f untouched for $((age/60)) min (management loop stalled?)"$'\n'
    fi
  fi
done

# Output only problems; silence = healthy
if [ -n "$issues" ]; then echo "AGENT-ECONOMY OPS ALERT ($(date -u +%FT%TZ))"; echo "$issues"; exit 1; fi
exit 0
