"""P3 MCP 端到端：确认 ctx 不暴露给 client，且 execute_step 不传 ctx 仍正常。"""
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
            est = next(t for t in tools.tools if t.name == "execute_step")
            props = list((est.inputSchema or {}).get("properties", {}).keys())
            print(f">>> execute_step 参数: {props}")
            assert "ctx" not in props, "ctx 暴露给 client 了！"
            print(">>> ctx 未暴露给 client ✓")

            r = parse(await session.call_tool("open_persistent_browser", {
                "user_data_dir": r"F:\github\auto_robot\demo\p3_e2e",
                "url": "https://example.com", "session_id": "p3_e2e",
            }))
            assert r.get("success"), r

            r = parse(await session.call_tool("execute_step", {
                "keyword": "Browser.Get Title", "arguments": [],
                "session_id": "p3_e2e", "raise_on_failure": False,
            }))
            print(f">>> execute_step(无 ctx) success={r.get('success')} "
                  f"title={r.get('result')!r}")
            assert r.get("success"), r

            c = parse(await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "p3_e2e",
            }))
            assert c.get("success"), c
            print("\n>>> P3 MCP 端到端通过 ✓")


if __name__ == "__main__":
    asyncio.run(main())
