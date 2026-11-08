"""实战验收：saucedemo 登录 + 加购物车 + 验证 + 产出可执行 .robot。

走真实 MCP 协议，模拟 AI agent 的完整调用序列。
"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PY = r"F:\github\auto_robot\.venv\Scripts\python.exe"
OUT = r"F:\github\auto_robot\demo\saucedemo_generated.robot"


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
                "scenario": "登录 saucedemo 并添加商品到购物车", "context": "web",
                "session_id": "saucedemo",
            }))
            print(f">>> [1] analyze_scenario success={d.get('success')}")

            d = parse(await session.call_tool("open_persistent_browser", {
                "user_data_dir": r"F:\github\auto_robot\demo\saucedemo_profile",
                "url": "https://www.saucedemo.com/", "session_id": "saucedemo",
            }))
            ok = d.get("success")
            print(f">>> [2] open_persistent_browser success={ok} err={(d.get('error') or '')[:70]}")
            if not ok:
                failures.append("open_persistent_browser")

            steps = [
                ("Browser.Fill Text", ["id=user-name", "standard_user"], "填写用户名"),
                ("Browser.Fill Text", ["id=password", "secret_sauce"], "填写密码"),
                ("Browser.Click", ["id=login-button"], "点击登录"),
                ("Browser.Get Text", ["css=.title"], "验证登录成功(Products)"),
                ("Browser.Click", ["id=add-to-cart-sauce-labs-backpack"], "加入购物车"),
                ("Browser.Get Text", ["css=.shopping_cart_badge"], "验证购物车数量"),
            ]
            for idx, (kw, args, label) in enumerate(steps, 3):
                d = parse(await session.call_tool("execute_step", {
                    "keyword": kw, "arguments": args, "session_id": "saucedemo",
                    "raise_on_failure": False,
                }))
                ok = d.get("success")
                result = d.get("result") or d.get("output")
                setv = d.get("assigned_variables") or d.get("session_variables")
                extra = f" result={str(result)[:30]}" if result else ""
                if setv and isinstance(setv, dict):
                    extra += f" vars={ {k: str(v)[:20] for k, v in setv.items()} }"
                print(f">>> [{idx}] {label} success={ok}{extra} "
                      f"self_healed={d.get('self_healed')} err={(d.get('error') or '')[:50]}")
                if not ok:
                    failures.append(label)

            d = parse(await session.call_tool("build_test_suite", {
                "test_name": "Saucedemo 登录加购物车", "session_id": "saucedemo",
            }))
            rf = d.get("rf_text") or ""
            print(f">>> [9] build_test_suite success={d.get('success')} robot_len={len(rf)}")
            if rf:
                with open(OUT, "w", encoding="utf-8") as f:
                    f.write(rf)
                print(f">>> 已保存 {OUT}")

            d = parse(await session.call_tool("manage_session", {
                "action": "close_session", "session_id": "saucedemo",
            }))
            print(f">>> [10] close_session success={d.get('success')}")

    if failures:
        print(f"\n>>> 失败步骤: {failures}")
        raise SystemExit(1)
    print("\n>>> 实战链路全部成功")


if __name__ == "__main__":
    asyncio.run(main())
