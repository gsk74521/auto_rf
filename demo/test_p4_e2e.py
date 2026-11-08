"""P4 MCP 端到端：fresh_profile / clean_state 参数透传。"""
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

            tools = await session.list_tools()
            opb = next(t for t in tools.tools if t.name == "open_persistent_browser")
            props = list((opb.inputSchema or {}).get("properties", {}).keys())
            print(f">>> open_persistent_browser 参数: {props}")
            assert "fresh_profile" in props and "clean_state" in props
            print(">>> fresh_profile / clean_state 已暴露 ✓")

            d = parse(await session.call_tool("open_persistent_browser", {
                "fresh_profile": True, "url": "https://example.com",
                "session_id": "p4_e2e_fresh",
            }))
            print(f">>> fresh_profile success={d.get('success')} "
                  f"dir={d.get('user_data_dir')}")
            assert d.get("success") and "robotmcp-fresh" in (d.get("user_data_dir") or ""), d
            await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "p4_e2e_fresh",
            })

            d = parse(await session.call_tool("open_persistent_browser", {
                "user_data_dir": r"F:\github\auto_robot\demo\p4_e2e_profile",
                "url": "https://www.saucedemo.com/", "session_id": "p4_e2e_clean",
                "clean_state": True,
            }))
            print(f">>> clean_state success={d.get('success')} "
                  f"state_cleaned={d.get('state_cleaned')}")
            assert d.get("success") and d.get("state_cleaned") is True, d
            await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "p4_e2e_clean",
            })

            print("\n>>> P4 MCP 端到端通过 ✓")


if __name__ == "__main__":
    asyncio.run(main())
