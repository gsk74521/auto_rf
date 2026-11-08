"""MCP 里第一次就调 open_persistent_browser（无前置关键字）。"""
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=r"F:\github\auto_robot\.venv\Scripts\python.exe",
        args=["-m", "robotmcp.server"], env=os.environ.copy(),
    )
    errlog = open("demo/mcp_stderr3.log", "w", encoding="utf-8", errors="replace")
    async with stdio_client(params, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            print(">>> init ok", flush=True)
            try:
                r = await asyncio.wait_for(s.call_tool("open_persistent_browser", {
                    "user_data_dir": "F:/github/auto_robot/demo/first_profile",
                    "url": "https://example.com/", "session_id": "f",
                }), 90)
                print(f">>> open(fresh): {r.content[0].text[:160]}", flush=True)
            except asyncio.TimeoutError:
                print(">>> open(fresh) TIMEOUT(90s)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
