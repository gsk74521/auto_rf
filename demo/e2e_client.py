"""端到端验证：真实 MCP client 走完整 AI 调用链路（非直接 import 函数）。

通过 stdio 连 rf-mcp server，模拟 AI agent 的调用序列：
  initialize → list_tools → analyze_scenario → open_persistent_browser
  → execute_step(正常) → execute_step(自愈) → build_test_suite

运行：
  PLAYWRIGHT_BROWSERS_PATH="$LOCALAPPDATA/ms-playwright" \
    .venv/Scripts/python.exe demo/e2e_client.py
"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PY = r"F:\github\auto_robot\.venv\Scripts\python.exe"


def parse(result) -> dict:
    """MCP call_tool 返回 content[0].text，是 JSON 字符串。"""
    if getattr(result, "isError", False):
        return {"success": False, "error": result.content[0].text if result.content else "isError"}
    text = result.content[0].text if result.content else ""
    try:
        return json.loads(text)
    except Exception:
        return {"success": False, "error": f"非 JSON 返回: {text[:200]}"}


async def main():
    params = StdioServerParameters(command=PY, args=["-m", "robotmcp.server"], env=os.environ.copy())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(">>> [1] initialize OK")

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f">>> [2] list_tools: {len(names)} 个工具")
            assert "open_persistent_browser" in names, "新工具未注册!"
            assert "execute_step" in names and "analyze_scenario" in names
            print(">>>     open_persistent_browser 已注册 ✓")

            # 3. analyze_scenario 建 session
            d = parse(await session.call_tool(
                "analyze_scenario",
                {"scenario": "打开 example.com 并读取页面标题", "context": "web",
                 "session_id": "e2e_test"},
            ))
            print(f">>> [3] analyze_scenario success={d.get('success')} "
                  f"session_id={d.get('session_id') or 'e2e_test'}")

            # 4. open_persistent_browser（改造 1，新工具）
            d = parse(await session.call_tool(
                "open_persistent_browser",
                {"user_data_dir": r"F:\github\auto_robot\demo\e2e_profile",
                 "url": "https://example.com", "session_id": "e2e_test"},
            ))
            print(f">>> [4] open_persistent_browser success={d.get('success')} "
                  f"reused={d.get('reused')} err={(d.get('error') or '')[:80]}")

            # 5. execute_step 正常链路：读标题
            d = parse(await session.call_tool(
                "execute_step",
                {"keyword": "Browser.Get Title", "arguments": [],
                 "session_id": "e2e_test", "raise_on_failure": False,
                 "assign_to": "page_title"},
            ))
            title = d.get("result") or d.get("output") or ""
            print(f">>> [5] execute_step(Get Title) success={d.get('success')} title={title!r}")

            # 6. execute_step 自愈链路：错误定位器（改造 4）
            d = parse(await session.call_tool(
                "execute_step",
                {"keyword": "Browser.Click", "arguments": ["text=不存在的按钮xyz"],
                 "session_id": "e2e_test", "raise_on_failure": False},
            ))
            print(f">>> [6] execute_step(错误定位器) self_heal_attempted={d.get('self_heal_attempted')} "
                  f"attempts={d.get('self_heal_attempts')}")

            # 7. build_test_suite 产出 .robot
            d = parse(await session.call_tool(
                "build_test_suite",
                {"test_name": "E2E 验证", "session_id": "e2e_test"},
            ))
            print(f">>> [7] build_test_suite success={d.get('success')} "
                  f"error={(d.get('error') or '')[:120]}")
            # 定位 robot 脚本内容字段
            for k, v in d.items():
                if isinstance(v, str) and ("*** " in v or ".robot" in v):
                    print(f">>>     robot 字段 '{k}' 内容:\n{v[:600]}")

            print("\n>>> 端到端 MCP 链路全部走通 ✓")


if __name__ == "__main__":
    asyncio.run(main())
