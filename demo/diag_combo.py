"""隔离变量：非主线程执行 + 可选 stdout 保护。"""
import asyncio
import concurrent.futures
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "plain"


async def main():
    if MODE == "protect":
        from robotmcp import server
        server._protect_mcp_stdout()
        print(">>> protect applied", flush=True)

    from robotmcp.components.execution.rf_native_context_manager import (
        RobotFrameworkNativeContextManager,
    )

    m = RobotFrameworkNativeContextManager()
    ex = concurrent.futures.ThreadPoolExecutor(1, thread_name_prefix="rf-exec")
    loop = asyncio.get_running_loop()

    await loop.run_in_executor(ex, lambda: m.create_context_for_session("x", ["Browser"]))
    print(">>> ctx ok", flush=True)

    r = await loop.run_in_executor(
        ex,
        lambda: m.execute_keyword_with_context(
            "x", "Browser.New Persistent Context",
            ["F:/github/auto_robot/demo/combo_profile", "chromium", "headless=True",
             "url=https://example.com"],
        ),
    )
    print(f">>> kw success={r.get('success')} err={str(r.get('error'))[:100]}", flush=True)


if __name__ == "__main__":
    if MODE == "anyio":
        import anyio
        anyio.run(main)
    else:
        asyncio.run(main())
