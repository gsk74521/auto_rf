"""P1 验收测试：生命周期状态机 + reuse_existing 透传。"""
import asyncio
from datetime import datetime, timedelta


def test_state_machine():
    from robotmcp import server
    sm = server.execution_engine.session_manager
    sess = sm.create_session("p1_test")
    assert sess.lifecycle_status == "active"
    print("[状态机] 新 session: active ✓")

    timeout = sm.config.SESSION_CLEANUP_TIMEOUT
    # 第一次超时：active → idle（keep-alive，不删）
    sess.last_activity = datetime.now() - timedelta(seconds=timeout + 10)
    sm.cleanup_expired_sessions()
    assert "p1_test" in sm.sessions, "ACTIVE session 不应被清理"
    assert sess.lifecycle_status == "idle"
    print("[状态机] 超时: active → idle (keep-alive 未删) ✓")

    # 再超时：idle → 移除
    sess.last_activity = datetime.now() - timedelta(seconds=timeout + 10)
    sm.cleanup_expired_sessions()
    assert "p1_test" not in sm.sessions, "IDLE session 应被清理"
    print("[状态机] 再超时: idle → 移除 ✓")


def test_revive():
    from robotmcp.models.session_models import ExecutionSession
    s = ExecutionSession(session_id="p1_revive")
    s.lifecycle_status = "idle"
    s.update_activity()
    assert s.lifecycle_status == "active"
    print("[状态机] idle 有活动 → 恢复 active ✓")


async def test_close_session():
    from robotmcp import server
    sm = server.execution_engine.session_manager
    sm.create_session("p1_close")
    r = await server.manage_session(action="close_session", session_id="p1_close")
    assert r.get("success"), r
    assert sm.get_session("p1_close") is None
    print("[close_session] 显式关闭后 session 已移除 ✓")


async def test_reuse_existing():
    from robotmcp import server
    r = await server.open_persistent_browser(
        reuse_existing=True, url="https://example.com", session_id="p1_reuse",
    )
    assert r.get("success"), r
    print("[reuse_existing] 复用模式开浏览器 + 导航成功 ✓")

    # close_session 释放真实浏览器
    c = await server.manage_session(action="close_session", session_id="p1_reuse")
    assert c.get("success"), c
    print("[reuse_existing] close_session 释放浏览器 ✓")


async def main():
    from robotmcp import server
    try:
        test_state_machine()
        test_revive()
        await test_close_session()
        await test_reuse_existing()
        print("\n=== P1 全部验收通过 ===")
    finally:
        server.execution_engine.session_manager.cleanup_all_sessions()
        server.execution_engine.keyword_executor._rf_exec.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
