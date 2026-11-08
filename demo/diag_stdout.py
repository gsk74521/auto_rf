"""决定性实验：直连 + 手动 _protect_mcp_stdout()，看是否复现卡住。"""
import asyncio


async def main():
    from robotmcp import server

    print(">>> import ok", flush=True)
    server._protect_mcp_stdout()
    print(">>> _protect_mcp_stdout applied", flush=True)

    try:
        r = await asyncio.wait_for(server.open_persistent_browser(
            user_data_dir="F:/github/auto_robot/demo/probe_profile",
            url="https://example.com/",
            session_id="probe",
        ), 60)
        print(f">>> open success={r.get('success')} err={(r.get('error') or '')[:80]}", flush=True)
    except asyncio.TimeoutError:
        print(">>> open TIMEOUT(60s) — 确认是 _protect_mcp_stdout 导致", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
