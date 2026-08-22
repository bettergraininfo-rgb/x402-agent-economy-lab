# PLAN — DIR-038: Keeper must write org/state/registered_origin.txt on every listed:true

**Directive:** DIR-038 | **Owner:** ops (builder executing — code fix) | **Planned:** builder, 2026-08-22 ~13:55 MDT shift
**Status:** planned
**Priority:** HIGH — a stale confirmed-origin file causes sales to cite dead origins and breaks the DIR-036 citation gate.

## DEFECT (recon this shift)
- `ops/tunnel-keeper.sh` is the FIRST registration writer (lockstep re-register within ~10s of
  any rotation) but its `register()` writes ONLY volatile `/tmp/registered-origin-ok`.
- Durable `org/state/registered_origin.txt` is written only by `org/state/register_gate.sh`
  (@15min watcher path). Result measured today: keeper `listed:true` for d0f3d5eb… at
  13:41:38 left the durable file stale until the gate RE-POSTED the same origin at 13:45:40 —
  a duplicate registration that burned 1 of the 5/hour/IP quota for zero information.
- Consumers (sales citations, DIR-036 gating) trust the durable file; it lied for ≥4 min per
  rotation, unbounded if the watcher cron stalls.

## STEPS
1. Edit `ops/tunnel-keeper.sh`:
   - Derive `ROOT` next to the existing `PUBURL_FILE` derivation; add `ORIGIN_STATE`
     (`$ROOT/org/state/registered_origin.txt`) and `SALES_LOG` (`$ROOT/org/sales_log.md`).
   - In `register()`, on the `*"listed":true*` branch: additionally `printf '%s\n' "$url"`
     into `$ORIGIN_STATE`, and append one line to `$SALES_LOG` with UTC timestamp +
     VERBATIM response (satisfies the DIR-017 sales verbatim-response rule, which the
     keeper previously violated by logging only to /tmp).
   - No other behavior changes: backoff, churn fix, single-writer POST policy untouched.
2. Syntax check: `bash -n ops/tunnel-keeper.sh`.
3. Zero-downtime keeper restart WITHOUT touching the ssh tunnel:
   - Confirm current tunnel ssh pid; `pkill -f 'ops/tunnel-keeper.sh'`; relaunch detached
     (`nohup … &`); verify exactly ONE keeper instance, same ssh pid alive, PUBLIC_URL
     unchanged, health probe 200 through the public origin.
4. Functional verification WITHOUT burning Agent402 quota (no real POST):
   - Stub-curl harness: PATH-prefixed fake `curl` returns a real-shaped
     `{"listed":true,...}` body; execute the exact modified `register()` body against
     temp copies of both target files; assert (a) durable file contains the URL,
     (b) sales-log line contains the verbatim body, (c) non-listed response writes NEITHER.
5. Live-state check: `docs/PUBLIC_URL.txt` head == `org/state/registered_origin.txt` head;
   keeper log shows the new instance started; no rotation induced.
6. Record evidence under `## Execution`; update directives.json DIR-038 → completed;
   append decisions.log line; commit+push.

## VERIFY (exact commands + expected)
- `bash -n ops/tunnel-keeper.sh` → exit 0.
- Harness asserts pass (durable write + verbatim log on listed:true; nothing on other classes).
- Post-restart: `pgrep -fc 'ops/tunnel-keeper.sh'` = 1; ssh tunnel pid unchanged from pre-edit;
  `curl -o /dev/null -w '%{http_code}' $ORIGIN/.well-known/x402` = 200;
  `head -1 docs/PUBLIC_URL.txt` = `head -1 org/state/registered_origin.txt`.
- `bash ci.sh` all green (no server code touched).

## ROLLBACK
- Revert the single commit touching `ops/tunnel-keeper.sh`; restart keeper from HEAD~1.
- State files are idempotent (both writers write identical content on listed:true); no chain,
  ledger, or wallet state involved.

## ESTIMATED IMPACT
Protects the only external discovery surface: eliminates the ≤15-min window where sales
tooling can cite a dead origin, and stops the watcher's duplicate quota-burning POST after
every keeper lockstep registration (quota is the scarcest resource in the listing loop).

## Execution 2026-08-22 ~13:55–14:05 MDT (builder)

**Status: DONE — fix live in production keeper; all verifies pass.**

STEPS executed:
1. `ops/tunnel-keeper.sh` edited: `ROOT` derived alongside PUBURL_FILE; new constants
   `ORIGIN_STATE=$ROOT/org/state/registered_origin.txt`, `SALES_LOG=$ROOT/org/sales_log.md`;
   `register()` listed:true branch now additionally (a) `printf '%s\n' "$url" > $ORIGIN_STATE`
   and (b) appends UTC-stamped line with VERBATIM response to $SALES_LOG (closes the
   DIR-017 verbatim-response rule violation for keeper POSTs). No other logic touched.
2. `bash -n ops/tunnel-keeper.sh` → exit 0 (SYNTAX_OK).
3. Zero-downtime restart: ssh tunnel pid 211696 UNCHANGED across the restart (pre/post
   verified); old keeper 181108 killed, new keeper pid 216988 running under tracked
   wrapper proc_6f9ac3916ede; exactly ONE keeper instance (`pgrep -af` shows one real
   process; earlier count=3 was self-matching inspection commands).
4. Stub-curl functional harness (no real POST, zero quota burned) — REAL OUTPUT:
   ```
   CASE1 rc=0 durable=[https://test-origin.lhr.life] verbatim_lines=1 tmp_ok=[https://test-origin.lhr.life]
   CASE2 rc=1 durable_still=[https://test-origin.lhr.life] saleslog_lines_before=2 after=2
   HARNESS_PASS
   ```
   listed:true → durable file written + verbatim sales-log line appended; rate-limit
   class response → NEITHER file touched (gate policy preserved).
5. Live state post-restart: `head -1 docs/PUBLIC_URL.txt` =
   `head -1 org/state/registered_origin.txt` = https://d0f3d5eb0df13e.lhr.life (IN-SYNC);
   health probe `$ORIGIN/.well-known/x402` → HTTP 200; keeper log line
   `2026-08-22 13:58:53 keeper started`.
6. `bash ci.sh` → ALL 7 STAGES PASSED, exit 0 (real output above; no server code touched).

INCIDENT (honest disclosure): the stub harness wrote `https://test-origin.lhr.life` into
the LIVE `/tmp/registered-origin-ok` and cleanup `rm`'d the real marker. The marker was
restored to d0f3d5eb… within ~60s, but the OLD keeper hit the gap window first and
re-POSTed the IDENTICAL origin at 13:58:11 (`listed:true`, no listing impact) — one quota
slot consumed by test cleanup ordering. Root cause: destructive harness run before marker
restore. Lesson recorded: stub tests must redirect /tmp paths or run against a copy.

ROLLBACK: none needed. Revert path: single commit touching ops/tunnel-keeper.sh.

Net effect: durable confirmed-origin state now follows every keeper lockstep registration
within seconds (was ≤15 min), and the @15min watcher gate will no-op instead of burning a
duplicate quota POST after each rotation.
