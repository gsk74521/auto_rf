"""P0 改造验收测试：改造 1（持久化浏览器）+ 改造 4（失败自愈）。

运行：
  PLAYWRIGHT_BROWSERS_PATH="$LOCALAPPDATA/ms-playwright" .venv/Scripts/python.exe demo/test_p0.py
"""
import asyncio


def test_helpers():
    from robotmcp import server as s
    assert s._is_locator_failure({"error": "could not find element by locator"})
    assert s._is_locator_failure({"error": "strict mode violation"})
    assert not s._is_locator_failure({"error": "expected 200 but got 500"})
    assert s._extract_locator(["text=登录"]) == "text=登录"
    assert s._extract_locator(["https://x.com", "css=button.x"]) == "css=button.x"
    cands = s._candidate_locators("text=登录按钮")
    assert any("xpath=" in c and "登录按钮" in c for c in cands), cands
    print("[改造4] 纯函数 OK, 候选:", cands)


async def test_persistent():
    from robotmcp import server as s
    profile = r"F:/github/auto_robot/demo/p0_profile"
    r1 = await s.open_persistent_browser(
        user_data_dir=profile, url="https://example.com", session_id="p0_test",
    )
    print("[改造1] 第1次:", {k: r1.get(k) for k in ("success", "reused", "error") if k in r1},
          str(r1.get("error") or "")[:100])
    assert r1.get("success"), r1

    # 第二次调用应复用（不重复 launch）
    r2 = await s.open_persistent_browser(
        user_data_dir=profile, session_id="p0_test",
    )
    print("[改造1] 第2次 reused:", r2.get("reused"), "success:", r2.get("success"))
    assert r2.get("success") and r2.get("reused") is True, r2


async def test_self_heal():
    from robotmcp import server as s
    await s.open_persistent_browser(
        user_data_dir=r"F:/github/auto_robot/demo/p0_profile2",
        url="https://example.com", session_id="p0_heal",
    )
    r = await s.execute_step(
        keyword="Browser.Click",
        arguments=["text=这个按钮肯定不存在xyz"],
        session_id="p0_heal",
        raise_on_failure=False,
    )
    print("[改造4] self_heal_attempted:", r.get("self_heal_attempted"),
          "| self_healed:", r.get("self_healed"),
          "| attempts:", r.get("self_heal_attempts"))
    if r.get("self_heal_dom"):
        print("[改造4] dom 摘要前 150 字:", str(r.get("self_heal_dom"))[:150].replace("\n", " "))
    assert r.get("success") is False, r
    assert r.get("self_heal_attempted") is True, r
    assert r.get("self_heal_dom") and r.get("self_heal_attempts"), r


async def main():
    from robotmcp import server
    try:
        test_helpers()
        await test_persistent()
        await test_self_heal()
        print("\n=== P0 全部验收通过 ===")
    finally:
        server.execution_engine.session_manager.cleanup_all_sessions()
        server.execution_engine.keyword_executor._rf_exec.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
