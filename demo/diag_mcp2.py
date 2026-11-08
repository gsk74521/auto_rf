"""MCP 里测 Browser 关键字（无浏览器时 Get Title 应快速报错，而非卡住）。"""
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=r"F:\github\auto_robot\.venv\Scripts\python.exe",
        args=["-m", "robotmcp.server"], env=os.environ.copy(),
    )
    errlog = open("demo/mcp_stderr2.log", "w", encoding="utf-8", errors="replace")
    async with stdio_client(params, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            print(">>> init ok", flush=True)

            for kw, args in [
                ("BuiltIn.Log", ["hello"]),
                ("Browser.Get Title", []),
                ("Browser.New Browser", ["chromium", "headless=True"]),
            ]:
                try:
                    r = await asyncio.wait_for(s.call_tool("execute_step", {
                        "keyword": kw, "arguments": args,
                        "session_id": "d", "raise_on_failure": False,
                    }), 45)
                    print(f">>> {kw}: {r.content[0].text[:100]}", flush=True)
                except asyncio.TimeoutError:
                    print(f">>> {kw}: TIMEOUT(45s)", flush=True)
                    return


if __name__ == "__main__":
    asyncio.run(main())
