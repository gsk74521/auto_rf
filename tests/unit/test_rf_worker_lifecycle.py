"""Closing a session must use its RF execution worker."""
import concurrent.futures
import threading
from types import SimpleNamespace

import pytest

from robotmcp.components.execution.session_manager import SessionManager


@pytest.mark.parametrize("libraries", [["Browser"], ["BuiltIn"]])
def test_close_uses_rf_worker(monkeypatch, libraries):
    calls = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as worker:
        owner = worker.submit(threading.get_ident).result()
        ctx = SimpleNamespace(
            _rf_exec=worker,
            _session_contexts={"owned": {"libraries": libraries, "imported_libraries": ["Browser"]}},
            execute_keyword_with_context=lambda *a: calls.append(threading.get_ident()) or {"success": True},
            cleanup_context=lambda *a: calls.append(threading.get_ident()),
        )
        monkeypatch.setattr(
            "robotmcp.components.execution.rf_native_context_manager.get_rf_native_context_manager",
            lambda: ctx,
        )
        SessionManager()._release_rf_context("owned")
    assert len(calls) == 2
    assert set(calls) == {owner}


def test_browser_children_do_not_inherit_mcp_stdin(monkeypatch):
    import subprocess
    import pytest
    browser = pytest.importorskip("Browser.playwright")
    from robotmcp.utils.browser_process import isolate_browser_stdin

    seen = []
    monkeypatch.setattr(browser, "Popen", lambda *a, **kw: seen.append(kw))
    monkeypatch.setattr(browser, "run", lambda *a, **kw: seen.append(kw))
    isolate_browser_stdin()
    isolate_browser_stdin()
    browser.Popen(["node", "wrapper.js"])
    browser.run(["node", "-v"])
    assert len(seen) == 2
    assert all(call["stdin"] == subprocess.DEVNULL for call in seen)


def test_closing_one_session_preserves_shared_rf_context():
    from robotmcp.components.execution.rf_native_context_manager import RobotFrameworkNativeContextManager
    manager = RobotFrameworkNativeContextManager()
    try:
        assert manager.create_context_for_session("first", ["BuiltIn"])["success"]
        assert manager.create_context_for_session("second", ["BuiltIn"])["success"]
        assert manager.cleanup_context("first")["success"]
        result = manager.execute_keyword_with_context("second", "BuiltIn.Set Variable", ["alive"])
        assert result.get("success"), result
        assert result.get("result") == "alive", result
    finally:
        manager.cleanup_context("second")
