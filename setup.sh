#!/bin/bash
set -e
cd ~/x402-agent-service
uv venv .venv --quiet || true
uv pip install --python .venv/bin/python --quiet fastapi "uvicorn[standard]" httpx
.venv/bin/python -c "import fastapi, httpx; print('deps ok')"
