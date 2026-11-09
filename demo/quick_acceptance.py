"""真实 MCP example.com 验收，并独立执行生成的 Robot 脚本。"""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo" / "example_generated.robot"


def parse(result):
    if getattr(result, "isError", getattr(result, "is_error", False)):
        raise AssertionError(result)
    data = json.loads(result.content[0].text)
    if not data.get("success"):
        raise AssertionError(data)
    return data


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "robotmcp.server"], env=os.environ.copy())
    with tempfile.TemporaryDirectory(prefix="rf-acceptance-") as profile:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), 30)
                print("initialize OK", flush=True)

                async def call(name, **kwargs):
                    data = parse(await asyncio.wait_for(session.call_tool(name, kwargs), 45))
                    print(name, "OK", flush=True)
                    return data

                await call("analyze_scenario", scenario="Open example.com and assert its title", context="web", session_id="quick")
                try:
                    await call("open_persistent_browser", user_data_dir=profile, clean_state=True,
                               url="https://example.com/", session_id="quick")
                    for keyword, arguments in [
                        ("Browser.Get Title", ["==", "Example Domain"]),
                        ("Browser.Get Element Count", ["css=a", ">=", "1"]),
                        ("Browser.Get Url", ["==", "https://example.com/"]),
                    ]:
                        await call("execute_step", keyword=keyword, arguments=arguments,
                                   session_id="quick", raise_on_failure=False)
                    data = await call("build_test_suite", test_name="Example acceptance", session_id="quick")
                    text = data.get("rf_text", "")
                    if "*** Test Cases ***" not in text or "Example Domain" not in text:
                        raise AssertionError(data)
                    text = text.replace(profile.replace("\\", "/"), "${OUTPUTDIR}${/}browser-profile")
                    OUT.write_text(text, encoding="utf-8")
                finally:
                    await call("manage_session", action="close_session", session_id="quick")
        subprocess.run(  # noqa: S603 - current interpreter and fixed Robot module
            [sys.executable, "-m", "robot", "--outputdir", str(ROOT / "demo" / "example_results"), str(OUT)],
            stdin=subprocess.DEVNULL, timeout=60, check=True,
        )
    print("MCP + independent Robot replay PASS", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
