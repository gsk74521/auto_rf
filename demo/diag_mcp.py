"""最小 MCP 诊断：区分是 MCP 层卡还是 Browser 库卡。"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=r"F:\github\auto_robot\.venv\Scripts\python.exe",
        args=["-m", "robotmcp.server"], env=os.environ.copy(),
    )
    errlog = open("demo/mcp_stderr.log", "w", encoding="utf-8", errors="replace")
    async with stdio_client(params, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            print(">>> init ok", flush=True)

            try:
                r = await asyncio.wait_for(s.call_tool("execute_step", {
                    "keyword": "BuiltIn.Log", "arguments": ["hello"], "session_id": "d",
                }), 60)
                print(f">>> BuiltIn.Log ok {r.content[0].text[:80]}", flush=True)
            except asyncio.TimeoutError:
                print(">>> BuiltIn.Log TIMEOUT(60s) — MCP 层卡", flush=True)
                return

            try:
                r = await asyncio.wait_for(s.call_tool("open_persistent_browser", {
                    "user_data_dir": "F:/github/auto_robot/demo/diag_profile",
                    "url": "https://example.com/", "session_id": "d",
                }), 90)
                print(f">>> open ok {r.content[0].text[:150]}", flush=True)
            except asyncio.TimeoutError:
                print(">>> open TIMEOUT(90s) — Browser 库在 MCP 子进程卡", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
