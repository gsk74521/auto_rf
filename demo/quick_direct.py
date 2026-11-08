"""快速实战（直连模式）：example.com → 执行 → build_test_suite → .robot。

不经过 MCP stdio，直接调用 server.py 的函数（与 test_p0 同一路径）。
"""
import asyncio


async def main():
    from robotmcp import server

    sid = "quick_direct"

    # 1. 开浏览器（持久化 + clean_state 重置业务状态）
    r = await server.open_persistent_browser(
        user_data_dir=r"F:/github/auto_robot/demo/quick_profile",
        clean_state=True,
        url="https://example.com/",
        session_id=sid,
    )
    print(f"[1] open          success={r.get('success')} err={(r.get('error') or '')[:60]}")

    # 2. 执行步骤
    steps = [
        ("Browser.Get Title", [], "标题"),
        ("Browser.Get Text", ["css=p >> nth=0"], "文本"),
        ("Browser.Get Element Count", ["css=a"], "链接数"),
        ("Browser.Get Url", [], "URL"),
    ]
    ok_all = True
    for kw, args, label in steps:
        d = await server.execute_step(
            keyword=kw, arguments=args, session_id=sid, raise_on_failure=False
        )
        val = d.get("result") if d.get("result") is not None else d.get("output")
        print(f"[2] {label:<6}      success={d.get('success')} "
              f"result={str(val)[:45] if val is not None else ''} "
              f"self_healed={d.get('self_healed')}")
        ok_all = ok_all and bool(d.get("success"))

    # 3. 生成 .robot
    d = await server.build_test_suite(test_name="Example 快速验收", session_id=sid)
    rf = d.get("rf_text") or ""
    print(f"[3] build_suite   success={d.get('success')} robot_len={len(rf)}")
    if rf:
        with open("demo/example_generated.robot", "w", encoding="utf-8") as f:
            f.write(rf)
        print("    saved demo/example_generated.robot")

    # 4. 关闭（真正释放浏览器）
    c = await server.manage_session(action="close_session", session_id=sid)
    print(f"[4] close_session success={c.get('success')}")

    print("\n" + ("=== 快速实战全部成功 ===" if ok_all and rf else "=== 有失败步骤 ==="))


if __name__ == "__main__":
    asyncio.run(main())
