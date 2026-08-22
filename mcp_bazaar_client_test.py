"""Smoke test for the MCP bazaar server using the official MCP client.

Boots the bazaar, then drives the MCP server over stdio exactly like a real
AI agent would: initialize -> list_tools -> call tools.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = os.path.dirname(os.path.abspath(__file__))


def wait_port(url: str, timeout: float = 15) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return True
        except Exception:
            time.sleep(0.4)
    return False


async def main() -> int:
    # Boot the bazaar the MCP server points at
    server_proc = subprocess.Popen(
        [f"{ROOT}/.venv/bin/uvicorn", "bazaar:app", "--port", "8502"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert wait_port("http://127.0.0.1:8502/health"), "bazaar failed to boot"
        print("[ok] bazaar running on :8502")

        params = StdioServerParameters(
            command=f"{ROOT}/.venv/bin/python",
            args=[f"{ROOT}/mcp_bazaar_server.py"],
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                print(f"[ok] MCP handshake — tools offered: "
                      f"{[t.name for t in tools.tools]}")

                res = await session.call_tool("list_services", {})
                catalog = json.loads(res.content[0].text)
                eps = [s["endpoint"] for s in catalog["services"]]
                print(f"[ok] list_services -> {eps}")

                res = await session.call_tool("buy_service", {
                    "endpoint": "/v1/sentiment",
                    "text": "MCP agents paying agents is great news",
                })
                purchase = json.loads(res.content[0].text)
                print(f"[ok] buy_service -> deliverable={purchase['deliverable']} "
                      f"paid=${purchase['paid_usdc']}")

                res = await session.call_tool("buy_service", {
                    "endpoint": "/v1/entity-extract",
                    "text": "Coinbase built Base where Virtuals lives",
                })
                purchase2 = json.loads(res.content[0].text)
                print(f"[ok] buy_service -> deliverable={purchase2['deliverable']} "
                      f"paid=${purchase2['paid_usdc']}")

                res = await session.call_tool("wallet_status", {})
                wallet = json.loads(res.content[0].text)
                print(f"[ok] wallet_status -> spent=${wallet['spent_usdc']} "
                      f"remaining=${wallet['remaining_usdc']}")

                assert wallet["purchases"], "no purchases recorded"
                print("\nALL MCP SMOKE TESTS PASSED")
                return 0
    finally:
        server_proc.terminate()


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
