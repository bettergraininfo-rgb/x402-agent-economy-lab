"""MCP server (SDK v2 API): exposes the agent bazaar as native tools.

Any MCP-compatible AI agent can connect over stdio and immediately discover
+ purchase bazaar services through the full x402 payment flow.

Tools:
  list_services   — free discovery
  buy_service     — x402 pay + deliverable + receipt
  wallet_status   — spend tracking

Run: .venv/bin/python mcp_bazaar_server.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from payment_core import PaymentPayload  # noqa: E402

BAZAAR_URL = os.environ.get("BAZAAR_URL", "http://127.0.0.1:8502")
AGENT_WALLET = os.environ.get("AGENT_WALLET", "0xMCP-AGENT-0001")
AGENT_BUDGET_USDC = float(os.environ.get("AGENT_BUDGET", "0.25"))

state = {"spent": 0.0, "purchases": []}


def _b64(o):
    return base64.b64encode(json.dumps(o).encode()).decode()


def _unb64(s):
    return json.loads(base64.b64decode(s))


def _hdr(headers, name):
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return None


# ------------------------------------------------------------- impls

async def list_services_impl() -> dict:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BAZAAR_URL}/bazaar")
        r.raise_for_status()
        return r.json()


async def buy_service_impl(endpoint: str, text: str, max_price: float | None) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(BAZAAR_URL + endpoint, params={"text": text})
        if r.status_code != 402:
            return {"error": f"unexpected status {r.status_code}", "body": r.json()}

        accepts = _unb64(_hdr(r.headers, "PAYMENT-REQUIRED"))
        price = float(accepts["amount_usdc"])

        if max_price is not None and price > max_price:
            return {"error": f"price ${price} exceeds your max {max_price}"}
        if state["spent"] + price > AGENT_BUDGET_USDC:
            return {"error": f"budget exhausted: spent ${state['spent']:.4f} "
                             f"of ${AGENT_BUDGET_USDC}"}

        payload = PaymentPayload(requirements=accepts, payer=AGENT_WALLET,
                                 amount_usdc=price)
        payload.sign()
        r2 = await c.get(BAZAAR_URL + endpoint, params={"text": text},
                         headers={"PAYMENT-SIGNATURE": _b64(payload.to_dict())})
        if r2.status_code != 200:
            return {"error": f"payment rejected: {r2.json()}"}

        receipt = _unb64(_hdr(r2.headers, "PAYMENT-RESPONSE"))
        state["spent"] += price
        state["purchases"].append({"endpoint": endpoint, "paid": price})
        return {"deliverable": r2.json(), "paid_usdc": price,
                "tx_hash": receipt["tx_hash"], "spent_total": round(state["spent"], 6)}


def wallet_status_impl() -> dict:
    return {"wallet": AGENT_WALLET, "spent_usdc": round(state["spent"], 6),
            "budget_usdc": AGENT_BUDGET_USDC,
            "remaining_usdc": round(AGENT_BUDGET_USDC - state["spent"], 6),
            "purchases": state["purchases"]}


# ------------------------------------------------------------ MCP glue

async def handle_list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=[
        types.Tool(name="list_services",
                   description="Discover services available in the x402 agent "
                               "bazaar (endpoint, price, description).",
                   inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="buy_service",
                   description="Purchase a bazaar service: pays the x402 price "
                               "from the agent wallet and returns deliverable "
                               "+ receipt.",
                   inputSchema={
                       "type": "object",
                       "properties": {
                           "endpoint": {"type": "string",
                                        "description": "e.g. /v1/sentiment"},
                           "text": {"type": "string"},
                           "max_price": {"type": "number",
                                         "description": "refuse above this"},
                       },
                       "required": ["endpoint", "text"],
                   }),
        types.Tool(name="wallet_status",
                   description="Agent wallet: spent, budget, remaining, log.",
                   inputSchema={"type": "object", "properties": {}}),
    ])


async def handle_call_tool(ctx, params: types.CallToolRequestParams):
    args = getattr(params, "arguments", None) or {}
    if params.name == "list_services":
        out = await list_services_impl()
    elif params.name == "buy_service":
        out = await buy_service_impl(args["endpoint"], args["text"],
                                     args.get("max_price"))
    elif params.name == "wallet_status":
        out = wallet_status_impl()
    else:
        out = {"error": f"unknown tool {params.name}"}
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(out, indent=2))])


app = Server("x402-bazaar-client",
             on_list_tools=handle_list_tools,
             on_call_tool=handle_call_tool)


async def main() -> None:
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
