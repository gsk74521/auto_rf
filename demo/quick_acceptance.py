"""快速实战验收：example.com 全链路（开浏览器 → 执行 → 生成 .robot）。

用 fresh_profile 避免状态污染，站点响应 <1s。
"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PY = r"F:\github\auto_robot\.venv\Scripts\python.exe"
OUT = r"F:\github\auto_robot\demo\example_generated.robot"


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
    failures = []

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(">>> [0] initialize OK")

            d = parse(await session.call_tool("analyze_scenario", {
                "scenario": "打开 example.com 并读取标题和内容", "context": "web",
                "session_id": "quick",
            }))
            print(f">>> [1] analyze_scenario success={d.get('success')}")

            d = parse(await session.call_tool("open_persistent_browser", {
                "user_data_dir": r"F:\github\auto_robot\demo\quick_profile",
                "clean_state": True,
                "url": "https://example.com/", "session_id": "quick",
            }))
            print(f">>> [2] open_persistent_browser success={d.get('success')} "
                  f"profile={d.get('user_data_dir')}")
            if not d.get("success"):
                failures.append("open")

            steps = [
                ("Browser.Get Title", [], "读标题"),
                ("Browser.Get Text", ["css=p >> nth=0"], "读文本"),
                ("Browser.Get Element Count", ["css=a"], "数链接"),
                ("Browser.Get Url", [], "读URL"),
            ]
            for idx, (kw, args, label) in enumerate(steps, 3):
                d = parse(await session.call_tool("execute_step", {
                    "keyword": kw, "arguments": args, "session_id": "quick",
                    "raise_on_failure": False,
                }))
                ok = d.get("success")
                result = d.get("result") or d.get("output")
                print(f">>> [{idx}] {label} success={ok} "
                      f"result={str(result)[:50] if result else ''} "
                      f"err={(d.get('error') or '')[:40]}")
                if not ok:
                    failures.append(label)

            d = parse(await session.call_tool("build_test_suite", {
                "test_name": "Example 快速验收", "session_id": "quick",
            }))
            rf = d.get("rf_text") or ""
            print(f">>> [7] build_test_suite success={d.get('success')} robot_len={len(rf)}")
            if rf:
                with open(OUT, "w", encoding="utf-8") as f:
                    f.write(rf)
                print(f">>> 已保存 {OUT}")

            d = parse(await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "quick",
            }))
            print(f">>> [8] close_session success={d.get('success')}")

    if failures:
        print(f"\n>>> 失败步骤: {failures}")
        raise SystemExit(1)
    print("\n>>> example.com 快速实战全部成功")


if __name__ == "__main__":
    asyncio.run(main())
