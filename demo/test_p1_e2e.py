"""P1 MCP 端到端：close_session + reuse_existing 通过真实 MCP 协议。"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PY = r"F:\github\auto_robot\.venv\Scripts\python.exe"


def parse(result):
    if getattr(result, "isError", False):
        return {"success": False, "error": result.content[0].text if result.content else "isError"}
    try:
        return json.loads(result.content[0].text)
    except Exception:
        return {"success": False, "error": "non-json"}


async def main():
    params = StdioServerParameters(
        command=PY, args=["-m", "robotmcp.server"], env=os.environ.copy()
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(">>> initialize OK")

            d = parse(await session.call_tool("open_persistent_browser", {
                "reuse_existing": True, "url": "https://example.com",
                "session_id": "p1_e2e",
            }))
            print(f">>> [1] open_persistent_browser(reuse_existing=True) "
                  f"success={d.get('success')} err={(d.get('error') or '')[:80]}")
            assert d.get("success"), d

            d = parse(await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "p1_e2e",
            }))
            print(f">>> [2] manage_session(close_session) success={d.get('success')} "
                  f"closed={d.get('closed')}")
            assert d.get("success"), d

            print("\n>>> P1 MCP 端到端通过 ✓")


if __name__ == "__main__":
    asyncio.run(main())
