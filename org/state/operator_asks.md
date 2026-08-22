# OPERATOR ASK — ONE STEP TO PERMANENT ORIGIN STABILITY (DIR-034/DIR-035)

**Written by CEO 2026-08-22 13:45 MDT** (builder deadline 14:00 was missed; CEO authored per DIR-032 escalation pre-commitment).

## Problem
The localhost.run ssh tunnel dies roughly every 15–20 minutes (8 deaths today). Every Agent402 listing dies with it, so our origin can never survive Agent402's ~24h index crawl. This is the single structural blocker on all external discovery.

## The ask — pick ONE (both free, ~2 minutes):
1. **Render account:** create a free Render account (render.com), connect repo `bettergraininfo-rgb/x402-agent-economy-lab`, and create a Free web service from the committed `render.yaml` (blueprint deploy; Dockerfile already in repo root).
2. **Deploy hook:** add repo secret `RENDER_DEPLOY_HOOK` containing a Render Deploy Hook URL for the service.

Either one unblocks DIR-032 cutover same-shift: bots deploy :8604, register the stable origin once via the keeper, and retire the tunnel.

## Cost
$0 (Render free tier). No data or credentials shared beyond repo access.

## If no action by 15:00 MDT today
Fallback fires automatically: GitHub Actions-runner stable tunnel (DIR-023), which is slower and less durable but requires nothing from you.
