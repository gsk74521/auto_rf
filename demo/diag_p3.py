"""诊断 get_page_source 在持久化 session 上的返回结构。"""
import asyncio


async def main():
    from robotmcp import server
    r = await server.open_persistent_browser(
        user_data_dir=r"F:/github/auto_robot/demo/p3_diag",
        url="https://example.com", session_id="p3_diag",
    )
    print("open:", r.get("success"), (r.get("error") or "")[:80])

    sess = server.execution_engine.session_manager.get_session("p3_diag")
    print("imported_libraries:", sess.imported_libraries)
    print("loaded_libraries:", sorted(sess.loaded_libraries))
    print("search_order:", sess.search_order)

    dom = await server.execution_engine.get_page_source(
        "p3_diag", full_source=False, filtered=True,
        filtering_level="standard", include_reduced_dom=True,
    )
    print("dom type:", type(dom).__name__)
    if isinstance(dom, dict):
        print("keys:", list(dom.keys()))
        for k, v in dom.items():
            if isinstance(v, str):
                print(f"  {k}: str len={len(v)} preview={v[:100]!r}")
            else:
                print(f"  {k}: {type(v).__name__} = {str(v)[:80]}")
    else:
        print("dom:", str(dom)[:300])

    await server.manage_session(action="close_session", session_id="p3_diag")


asyncio.run(main())
