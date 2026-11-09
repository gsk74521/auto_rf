# auto_rf · Robot Framework MCP Enhanced

[简体中文](README.md) | **English**

> **Based on [rf-mcp v0.36.0](https://github.com/manykarim/rf-mcp) by Many Kasiriha.** This derivative work retains the upstream [Apache-2.0 license](LICENSE) and copyright notices. See [NOTICE](NOTICE).

Write and debug automation with an AI assistant, keep the browser open between steps, and export executable Robot Framework `.robot` suites.

`auto_rf` is an MCP server. The distribution is **`rf-mcp-enhanced`**; the import module remains `robotmcp`, and the CLI commands remain `robotmcp` / `rf-mcp`.

[Release v0.37.1](https://github.com/gsk74521/auto_rf/releases/tag/v0.37.1) · [Detailed usage (Chinese)](USAGE_ZH.md) · [Packaging (Chinese)](PUBLISH_ZH.md)

## Workflow

Instead of generating an entire script and reopening the browser after every failure, validate keywords one at a time in the same server process and session. Inspect the current DOM and retry the failed step, then export a suite for independent execution.

```text
analyze_scenario → discover keywords → open_persistent_browser
                → execute_step → inspect DOM / repair / retry in the same session
                → build_test_suite → save .robot → run with Robot Framework
```

## Enhancements

| Capability | Behavior |
| --- | --- |
| Persistent browser | Reuses the live context within a session and saves the profile to disk. Login persistence depends on the site's storage and expiry rules. |
| Locator recovery | Captures DOM evidence, tries rule-based candidates, then optionally asks the MCP host through sampling. Recovery is not guaranteed. |
| Lifecycle | Tracks active/idle/closed states and provides explicit `close_session` cleanup. |
| Browser reuse | Passes `reuse_existing` to Browser Library for browsers managed by that library. |
| State control | Supports fresh profiles and clearing localStorage/sessionStorage while retaining cookies. |
| Windows stdio stability | v0.37.1 isolates Browser subprocess stdin, removes startup browser warmup, and uses a dedicated worker for RF execution and cleanup. |

Upstream keyword discovery, suite generation and optional web/API/mobile/database integrations remain available. See the [tool reference](docs/MCP_TOOLS.md) for inherited tools and [USAGE_ZH.md](USAGE_ZH.md) for fork-specific behavior.

## Requirements

- Python **3.11+ recommended for Browser 21**; the core package supports Python 3.10+.
- Node.js LTS for Browser Library's Node wrapper.
- A browser revision matching the installed Browser Library version.
- An MCP-compatible AI client; sampling support is required only for LLM recovery.
- [uv](https://docs.astral.sh/uv/) recommended.

This release was validated on Windows 11, Python 3.14 and Browser 21.0.0. Other platforms and Browser versions were not validated in this release.

## Install from source

```bash
git clone https://github.com/gsk74521/auto_rf.git
cd auto_rf
uv sync --extra web
```

Activate the environment so subsequent commands use this project's interpreter:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
# Git Bash on Windows: source .venv/Scripts/activate
```

Initialize the Node wrapper and install Chromium:

```bash
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium
```

Other extras include `api`, `mobile`, `database`, `frontend` and `memory`. `uv sync --extra all` combines integrations but excludes `desktop` and `semantic`.

## Install a release wheel

Download the wheel from [Releases](https://github.com/gsk74521/auto_rf/releases), then run in an empty directory:

```bash
uv venv --python 3.11
# Activate this environment as shown above, then:
uv pip install "./rf_mcp_enhanced-0.37.1-py3-none-any.whl[web]"
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium
robotmcp --version
```

The `[web]` extra installs Browser and Selenium libraries; a bare wheel does not include them. Install this fork from source or release assets. `pip install rf-mcp` installs upstream.

### Browser cache and a mirror for users in China

To reuse an existing cache, set the path **before installation and server startup**. Its revision must match Browser Library; Browser 21.0.0 in our verification used Chromium revision 1248.

```powershell
# Windows PowerShell
$env:PLAYWRIGHT_BROWSERS_PATH = "$env:LOCALAPPDATA/ms-playwright"
# Optional mirror:
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://registry.npmmirror.com/-/binary/playwright"
python -m Browser.entry install chromium
```

```bash
# Git Bash on Windows
export PLAYWRIGHT_BROWSERS_PATH="$LOCALAPPDATA/ms-playwright"
export PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
python -m Browser.entry install chromium
```

Mirror availability varies by revision. On a 404, unset `PLAYWRIGHT_DOWNLOAD_HOST` and retry the official source. `Executable doesn't exist` usually means a cache path or revision mismatch. Use separate caches for different Browser versions when needed.

## Configure your MCP client

Use the **absolute path to the interpreter where this fork is installed**. Example for a Windows source checkout (replace all paths):

```json
{
  "mcpServers": {
    "robotmcp": {
      "command": "C:/work/auto_rf/.venv/Scripts/python.exe",
      "args": ["-m", "robotmcp.server"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "C:/Users/YOUR_USER/AppData/Local/ms-playwright"
      }
    }
  }
}
```

On Linux/macOS, the interpreter is typically `/absolute/path/auto_rf/.venv/bin/python`. The configuration container differs by client; this example uses `mcpServers`. Omit the custom cache entry if using Browser's default location. Your custom RF libraries must also be installed in the server's Python environment.

Start manually with `python -m robotmcp.server` when needed. It defaults to stdio; stdout is reserved for MCP protocol messages.

## Ask the agent to write a test

```text
Use robotmcp and Browser Library to open https://www.saucedemo.com/.
Log in with standard_user / secret_sauce, add the first product to the cart,
and assert that the cart count is 1.
Discover keywords before using them. Keep the same session_id and browser
throughout debugging. On failure, inspect the current DOM and retry the failed
step. Generate a .robot suite after all steps pass, save it, and run it
independently with Robot Framework. Close the session when finished.
```

## Browser modes

These are MCP tool arguments, not standalone Python programs:

```python
# Persistent profile (default)
open_persistent_browser(session_id="s1", url="https://example.com/", headless=False)
# Reuse a browser managed by Browser Library
open_persistent_browser(session_id="s1", reuse_existing=True)
# New temporary profile
open_persistent_browser(session_id="s2", fresh_profile=True, url="https://example.com/")
# Clear localStorage/sessionStorage on opening, retaining cookies
open_persistent_browser(session_id="s3", clean_state=True, url="https://example.com/")
# Explicit cleanup
manage_session(action="close_session", session_id="s1")
```

- Keep the same `session_id` for subsequent steps. The default profile is `~/.robotmcp/browser-profiles/<session_id>/`; use `user_data_dir` to change it.
- `headless=True` is the default. Use `headless=False` for visible debugging.
- An already open persistent context returns `reused=True` immediately. New URL, profile and cleaning options are not applied on this path. Navigate through `execute_step`, or close and reopen to change the profile/clean state.
- `clean_state` can remove login state stored in localStorage/sessionStorage. `fresh_profile` starts without existing cookies too; temporary directories require manual cleanup.
- `reuse_existing` does not attach to arbitrary manually opened Chrome instances.
- `build_test_suite` returns `rf_text`; save it as a `.robot` file. Read-only inspection steps may be omitted unless recorded (`record=True`) or assigned (`assign_to`). Include assertions, then validate independently.

## Acceptance checks

Run from a **source checkout**, with its environment active and the matching browser installed:

```bash
python demo/run_acceptance.py quick_acceptance --timeout 120
python demo/run_acceptance.py real_world_acceptance --timeout 120
```

Both use real MCP stdio, assert actual values, generate a suite, and replay it in a separate Robot process. The wrapper preserves nonzero exit codes; timeout returns **124** and terminates that run's process tree. Scripts are in the repository, not the installed wheel.

For v0.37.1, targeted regression reported **154 passed / 5 skipped**, and P0/P1/P3/P4 passed. The wheel was installed into a new environment: example.com and SauceDemo each completed the MCP flow and independent Robot replay (**1/1 PASS** each). Startup without a browser and process cleanup were also checked. The entire upstream test suite was not run.

## Current limits

- RF/Browser state is shared inside one process. Multiple browser sessions are **not isolated**; closing one can affect others. Use separate MCP server processes for isolation.
- Profiles preserve state, not live tabs across server restarts. Login persistence depends on the website.
- Sampling depends on the host. P3 used a fixed-response substitute and did not measure real model repair quality.
- Cancelling an asyncio wait cannot forcibly stop synchronous third-party keywords. The acceptance process timeout is not a hard server-side timeout guarantee for every keyword.
- The Browser Node driver may remain alive until server shutdown even after Chromium closes.

## Documentation and license

| Document | Purpose |
| --- | --- |
| [中文 README](README.md) | Chinese quick start |
| [Usage guide](USAGE_ZH.md) | Detailed fork tools and troubleshooting (Chinese) |
| [Architecture](二次开发架构设计.md) | Design notes (Chinese) |
| [Packaging](PUBLISH_ZH.md) | Distribution instructions (Chinese) |
| [v0.37.1 notes](release/RELEASE_NOTES_v0.37.1.md) | Fixes and verification scope |
| [Tools](docs/MCP_TOOLS.md) / [Configuration](docs/CONFIGURATION.md) / [Examples](docs/EXAMPLES.md) | Inherited upstream features; upstream installation examples may need adaptation for this fork |

Licensed under **Apache-2.0**. Retain [LICENSE](LICENSE), upstream copyright notices and [NOTICE](NOTICE) when redistributing. Upstream: [manykarim/rf-mcp](https://github.com/manykarim/rf-mcp).
