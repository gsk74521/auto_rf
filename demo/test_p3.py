"""P3 验收测试：LLM 兜底自愈（规则全败 → 宿主 sampling 生成定位器）。

用 FakeCtx 模拟宿主 sampling，验证「LLM 分支」代码路径。
真实 LLM 能力需宿主支持 sampling，这里不依赖。
"""
import asyncio


class FakeCtx:
    """模拟 FastMCP Context.sample()，返回预设定位器。"""

    def __init__(self, locator):
        self.locator = locator
        self.called = False
        self.last_prompt = None

    async def sample(self, **kwargs):
        self.called = True
        self.last_prompt = kwargs.get("messages")

        class R:
            text = self.locator
        return R()


def test_clean_locator():
    from robotmcp import server
    assert server._clean_locator("```\ntext=登录\n```") == "text=登录"
    assert server._clean_locator('"css=#btn"') == "css=#btn"
    assert server._clean_locator("Here is the locator:\ntext=登录") == "text=登录"
    assert server._clean_locator("xpath=//button[contains(.,'登录')]") == "xpath=//button[contains(.,'登录')]"
    assert server._clean_locator("no locator here") is None
    print("[P3] _clean_locator 清洗 OK")


async def test_llm_locator_suggest():
    from robotmcp import server
    ctx = FakeCtx("text=More information")
    got = await server._llm_suggest_locator(
        ctx, "Browser.Click", "text=MoreInfo",
        "<a href='https://www.iana.org/domains/example'>More information...</a>",
        "TimeoutError: locator.click",
    )
    assert got == "text=More information", got
    assert ctx.called and ctx.last_prompt and "Browser.Click" in ctx.last_prompt
    print("[P3] _llm_suggest_locator + prompt 构造 OK")


async def test_self_heal_llm_fallback():
    from robotmcp import server
    r = await server.open_persistent_browser(
        user_data_dir=r"F:/github/auto_robot/demo/p3_profile",
        url="https://example.com", session_id="p3_test",
    )
    assert r.get("success"), r

    # 错误定位器（规则候选也会失败），FakeCtx 返回能命中的定位器
    ctx = FakeCtx("text=Learn more")
    res = await server._self_heal_step(
        "p3_test", "Browser.Click", ["text=MoreInfo"],
        {"error": "TimeoutError: locator.click: Timeout 10000ms exceeded"},
        ctx=ctx,
    )
    print(f"[P3] llm_called={ctx.called} self_healed={res.get('self_healed')} "
          f"by={res.get('self_healed_by')} locator={res.get('healed_locator')}")
    assert ctx.called, "LLM 未被调用"
    assert res.get("success") and res.get("self_healed"), res
    assert res.get("self_healed_by") == "llm", res

    await server.manage_session(action="close_session", session_id="p3_test")


async def main():
    from robotmcp import server
    try:
        test_clean_locator()
        await test_llm_locator_suggest()
        await test_self_heal_llm_fallback()
        print("\n=== P3 全部验收通过 ===")
    finally:
        server.execution_engine.session_manager.cleanup_all_sessions()
        server.execution_engine.keyword_executor._rf_exec.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
