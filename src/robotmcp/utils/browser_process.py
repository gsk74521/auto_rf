"""Keep Browser's Node children away from the MCP transport's stdin."""
from functools import wraps
from subprocess import DEVNULL


def isolate_browser_stdin() -> None:
    # Browser imports Popen/run into this module. Patch only those entry points,
    # never subprocess globally. Inheriting a pending Windows pipe read can
    # prevent Node startup and leave Browser waiting forever on gRPC Health.
    import Browser.playwright as playwright

    for name in ("Popen", "run"):
        original = getattr(playwright, name)
        if getattr(original, "_robotmcp_stdin_isolated", False):
            continue

        def wrap(target):
            @wraps(target)
            def isolated(*args, **kwargs):
                kwargs.setdefault("stdin", DEVNULL)
                return target(*args, **kwargs)
            isolated._robotmcp_stdin_isolated = True
            return isolated

        setattr(playwright, name, wrap(original))
