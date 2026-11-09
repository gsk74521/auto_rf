"""验证 close_session 是否真正释放浏览器进程（改造 2 的核心价值）。"""
import asyncio
import time

import psutil


def browser_pids():
    pids = set()
    for p in psutil.Process().children(recursive=True):
        try:
            name = p.name().lower()
            if "chrom" in name or "headless" in name:
                pids.add(p.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


async def main():
    from robotmcp import server

    before = browser_pids()
    r = await server.open_persistent_browser(
        user_data_dir=r"F:/github/auto_robot/demo/p1_profile",
        url="https://example.com", session_id="p1_pid",
    )
    assert r.get("success"), r
    await asyncio.sleep(1.5)
    opened = browser_pids() - before
    print(f"开后新增浏览器 PID: {sorted(opened)}")
    assert opened, "No owned Chromium process was observed; release check would be vacuous"

    c = await server.manage_session(action="close_session", session_id="p1_pid")
    assert c.get("success"), c
    await asyncio.sleep(2.5)
    survived = opened & browser_pids()
    print(f"close_session 后仍存活: {sorted(survived)}")
    if survived:
        print("❌ 浏览器未真正释放（end_suite 未触发 Browser 关闭）")
        return 1
    print("✅ 浏览器进程已真正释放")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
