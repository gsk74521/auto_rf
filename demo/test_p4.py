"""P4 验收：fresh_profile（临时全新 profile）+ clean_state（清空业务状态）。"""
import asyncio


async def _step(session_id, kw, args):
    from robotmcp import server
    return await server.execute_step(
        keyword=kw, arguments=args, session_id=session_id, raise_on_failure=False
    )


async def test_fresh_profile():
    from robotmcp import server
    r = await server.open_persistent_browser(
        fresh_profile=True, url="https://example.com", session_id="p4_fresh",
    )
    assert r.get("success"), r
    profile = r.get("user_data_dir", "")
    print("[fresh_profile] profile:", profile)
    assert "robotmcp-fresh" in profile, profile
    print("[fresh_profile] 使用临时全新目录 ✓")
    await server.manage_session(action="close_session", session_id="p4_fresh")


async def test_clean_state():
    from robotmcp import server
    profile = r"F:/github/auto_robot/demo/p4_clean_profile2"

    # 1) 打开 saucedemo，登录 + 加购（写入 localStorage cart-contents）
    r = await server.open_persistent_browser(
        user_data_dir=profile, url="https://www.saucedemo.com/", session_id="p4_clean",
    )
    assert r.get("success"), r
    for kw, args in [
        ("Browser.Fill Text", ["id=user-name", "standard_user"]),
        ("Browser.Fill Text", ["id=password", "secret_sauce"]),
        ("Browser.Click", ["id=login-button"]),
        ("Browser.Click", ["id=add-to-cart-sauce-labs-backpack"]),
    ]:
        d = await _step("p4_clean", kw, args)
        assert d.get("success"), (kw, d)
    d = await _step("p4_clean", "Browser.Evaluate JavaScript",
                    ["${None}", "() => JSON.stringify(localStorage)"])
    before = d.get("result") or d.get("output")
    print("[clean_state] 加购后 localStorage:", before)
    assert "cart-contents" in str(before), before
    await server.manage_session(action="close_session", session_id="p4_clean")

    # 2) 同 profile 重开，clean_state=True
    r = await server.open_persistent_browser(
        user_data_dir=profile, url="https://www.saucedemo.com/",
        session_id="p4_clean2", clean_state=True,
    )
    assert r.get("success"), r
    print("[clean_state] state_cleaned:", r.get("state_cleaned"))
    assert r.get("state_cleaned") is True, r

    # 3) 确认 localStorage 已清空
    d = await _step("p4_clean2", "Browser.Evaluate JavaScript",
                    ["${None}", "() => JSON.stringify(localStorage)"])
    after = d.get("result") or d.get("output")
    print("[clean_state] 清理后 localStorage:", after)
    assert "cart-contents" not in str(after), after

    # 4) 重新登录后按钮恢复（clean_state 清空了业务状态，含 saucedemo 的登录标记）
    for kw, args in [
        ("Browser.Fill Text", ["id=user-name", "standard_user"]),
        ("Browser.Fill Text", ["id=password", "secret_sauce"]),
        ("Browser.Click", ["id=login-button"]),
    ]:
        d = await _step("p4_clean2", kw, args)
        assert d.get("success"), (kw, d)
    # 等商品列表渲染（React 异步）
    d = await _step("p4_clean2", "Browser.Wait For Elements State",
                    ["css=.inventory_item >> nth=0", "visible"])
    assert d.get("success"), d
    d = await _step("p4_clean2", "Browser.Get Element Count", ["css=.inventory_item"])
    assert d.get("success"), d
    count = d.get("result", d.get("output"))
    assert str(count) == "6", d
    print("[clean_state] 重新登录后商品数:", count)
    d = await _step("p4_clean2", "Browser.Get Element Count",
                    ["id=add-to-cart-sauce-labs-backpack"])
    cnt = d.get("result") or d.get("output")
    print("[clean_state] 重新登录后 add-to-cart 按钮数:", cnt)
    assert str(cnt) == "1", cnt
    print("[clean_state] 业务状态重置，按钮恢复 ✓")
    await server.manage_session(action="close_session", session_id="p4_clean2")


async def main():
    from robotmcp import server
    try:
        await test_fresh_profile()
        await test_clean_state()
        print("\n=== P4 全部验收通过 ===")
    finally:
        server.execution_engine.session_manager.cleanup_all_sessions()
        server.execution_engine.keyword_executor._rf_exec.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
