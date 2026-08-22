#!/bin/bash
set -e
cd ~/x402-agent-service
echo "--- trying official x402 sdk ---"
uv pip install --python .venv/bin/python x402 2>&1 | tail -3 || echo "x402 pkg unavailable"
echo "--- trying cdp sdk ---"
uv pip install --python .venv/bin/python cdp-sdk 2>&1 | tail -3 || echo "cdp-sdk unavailable"
.venv/bin/python - <<'EOF'
for mod in ("x402", "cdp"):
    try:
        __import__(mod)
        print(f"{mod}: INSTALLED")
    except ImportError as e:
        print(f"{mod}: not importable ({e})")
EOF
