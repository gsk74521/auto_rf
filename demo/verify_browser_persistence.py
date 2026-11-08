"""最小 demo：验证 rf-mcp 同一 session 内 execute_step 连续执行时，浏览器是否只开一次。

命题：AI 写脚本反复调试低效的根因是「每次跑都重开浏览器」。
rf-mcp 声称用 session 常驻浏览器。本脚本用真实的 ExecutionCoordinator
（rf-mcp 实际执行路径）连续执行多条关键字，对比 chromium 进程 PID 是否保持不变。
"""
import asyncio
import sys
import time

import psutil

from robotmcp.components.execution.execution_coordinator import ExecutionCoordinator


def chromium_pids() -> set:
    """枚举当前机器上浏览器「主进程」PID（chromium/headless_shell，排除 --type= 渲染子进程）。

    chromium 是多进程架构，打开新页面会 spawn renderer/gpu 子进程，这些不是「重开浏览器」。
    只统计不含 --type= 的主进程，才能准确判断浏览器是否被重开。
    """
    pids = set()
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (p.info["name"] or "").lower()
            cmd = list(p.info["cmdline"] or [])
            cmd_str = " ".join(cmd).lower()
            if not any(t in name or t in cmd_str for t in ("chrom", "headless", "playwright")):
                continue
            if any("--type=" in c for c in cmd):
                continue  # renderer/gpu/utility 子进程，非浏览器主进程
            pids.add(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


async def main():
    coord = ExecutionCoordinator()
    sid = "demo_session"

    before = chromium_pids()

    # 1) 开浏览器（Library.Keyword 前缀强制 import Browser 库）
    r = await coord.execute_step("Browser.New Browser", ["chromium", "headless=True"], session_id=sid)
    print(f"[1] New Browser   success={r.get('success')}  err={(r.get('error') or '')[:120]}")
    await asyncio.sleep(1.5)
    after_browser = chromium_pids()
    new_pids = after_browser - before
    print(f"    浏览器进程 PID: {sorted(new_pids) or '无'}")

    # 2) 打开页面
    r = await coord.execute_step("Browser.New Page", ["https://example.com"], session_id=sid)
    print(f"[2] New Page      success={r.get('success')}  err={(r.get('error') or '')[:120]}")

    # 3) 读标题
    r = await coord.execute_step("Browser.Get Title", [], session_id=sid)
    title = r.get("result") or r.get("output") or r.get("error") or ""
    print(f"[3] Get Title     success={r.get('success')}  result={str(title)[:80]}")

    # 4) 读 URL（验证状态保持：不重新 New Browser，直接读当前页）
    r = await coord.execute_step("Browser.Get Url", [], session_id=sid)
    url = r.get("result") or r.get("output") or r.get("error") or ""
    print(f"[4] Get Url       success={r.get('success')}  result={str(url)[:80]}")

    # 5) 结论：浏览器进程是否保持同一批
    final = chromium_pids()
    survived = new_pids & final
    reopened = bool((final - before) - new_pids)
    print("\n===== 结论 =====")
    print(f"第1步后浏览器 PID: {sorted(new_pids) or '无'}")
    print(f"第4步后仍存活 PID: {sorted(survived) or '无'}")
    print(f"浏览器在同一 session 内保持常驻: {'是 ✅' if survived else '否 ❌'}")
    print(f"后续步骤重开了新浏览器进程:     {'是 ❌' if reopened else '否 ✅'}")

    if survived and not reopened:
        print("\n>>> 验证通过：session 内浏览器常驻，无需重复打开。")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
