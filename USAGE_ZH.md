# rf-mcp 增强版 使用说明

> 基于 [rf-mcp](https://github.com/manykarim/rf-mcp) 二次开发的 Robot Framework MCP Server。
> 核心解决：**AI 写自动化时反复打开浏览器调试、效率低**。
>
> 本版本在 rf-mcp v0.36.0 基础上增加了 4 项增强 + 2 个关键修复，均已通过真实 MCP 端到端验证。

---

## 1. 这是什么

一个 **MCP Server**，让 AI 编码助手（Claude Code / Cursor / Claude Desktop 等）能够：

1. 逐步执行 Robot Framework 关键字，**浏览器在同一会话内常驻**（不重开）
2. 失败时**自动抓 DOM + 规则/LLM 修复定位器并重试**
3. 全部步骤验证通过后，生成**可执行的 .robot 脚本**

典型工作流（AI 自动完成）：

```
analyze_scenario → open_persistent_browser → execute_step（逐条验证）
                 → 失败自动自愈 → build_test_suite → 产出 .robot
```

---

## 2. 相比上游 rf-mcp 的增强

| 编号 | 增强 | 解决的问题 |
|---|---|---|
| P0 | `open_persistent_browser` 持久化浏览器 + SingletonLock 清理 | 关掉重开、进程 crash 后免重新登录 |
| P0 | 规则版失败自愈（text→xpath contains 等） | 定位器轻微漂移时自动修复 |
| P1 | 会话生命周期状态机（active/idle/closed）+ `close_session` | 浏览器进程不泄漏，调试中不被误关 |
| P1 | `reuse_existing` 透传 | 复用 AI 已开的浏览器 |
| P3 | LLM 兜底自愈（宿主 sampling） | 规则修不好时让 LLM 生成定位器 |
| P4 | `fresh_profile` / `clean_state` | 持久化 profile 的业务状态污染（购物车等） |
| 修复 | Browser 库登记 + `end_suite` 不关浏览器 | DOM 抓不到、`close_session` 假释放 |

---

## 3. 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | ≥ 3.10（本机 3.14） | |
| Node.js | 任意 LTS（本机 v24） | robotframework-browser 的 node wrapper 需要 |
| Playwright 浏览器 | chromium 等 | 可复用系统已装的（见下方 `PLAYWRIGHT_BROWSERS_PATH`） |
| uv | 推荐 | 用于安装和管理环境 |

---

## 4. 安装

### 4.1 从源码安装（当前目录）

```bash
cd F:/github/auto_robot

# 安装全部依赖（Browser + Selenium + Appium + Requests + Database + 前端 + 记忆）
uv sync --extra all

# 初始化 robotframework-browser 的 node wrapper（浏览器二进制已装则跳过下载）
.venv/Scripts/python.exe -m Browser.entry init --skip-browsers
```

### 4.2 从 wheel 安装（发布后）

```bash
uv pip install rf_mcp_enhanced-0.37.0-py3-none-any.whl
# 然后初始化 node wrapper
python -m Browser.entry init --skip-browsers
```

### 4.3 浏览器（关键）

robotframework-browser 需要**版本匹配**的 Playwright 浏览器。三种做法选一：

**方式 A：官方下载**

```bash
python -m Browser.entry install chromium
```

**方式 B：国内镜像（国内用户推荐，速度快）**

```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
python -m Browser.entry install chromium
```

> 镜像只同步较新版本（CfT 148+）。若项目锁定旧版 browser（如 19.12.7 → CfT 145），
> 镜像没有对应文件，需用方式 A 或把 browser 升到新版。

**方式 C：复用系统已装的 Playwright 浏览器**

robotframework-browser 默认去自己 wrapper 下的 `.local-browsers` 找浏览器，
与系统 Playwright 缓存（`%LOCALAPPDATA%/ms-playwright`）不是同一处。若想复用：

```bash
export PLAYWRIGHT_BROWSERS_PATH="$LOCALAPPDATA/ms-playwright"
```

> **注意**：系统缓存里的浏览器版本必须与 robotframework-browser 要求的版本一致
> （例如 browser 19.12 → chromium-1208）。版本不一致会报
> `Executable doesn't exist at ...chromium_headless_shell-XXXX...`——此时改用方式 A。

---

## 5. 配置到 AI 客户端（MCP）

### 5.1 自动安装

```bash
cd F:/github/auto_robot
robotmcp install     # 自动写入 Claude Code / Cursor / Codex 等配置
robotmcp doctor -C .  # 检查环境
```

### 5.2 手动配置（通用 JSON）

```json
{
  "mcpServers": {
    "robotmcp": {
      "command": "F:/github/auto_robot/.venv/Scripts/python.exe",
      "args": ["-m", "robotmcp.server"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "C:/Users/<你>/AppData/Local/ms-playwright"
      }
    }
  }
}
```

### 5.3 Claude Code

```bash
claude mcp add rf-mcp -- F:/github/auto_robot/.venv/Scripts/python.exe -m robotmcp.server
```

---

## 6. 快速开始

在 AI 助手里说：

> 用 robotmcp 登录 https://www.saucedemo.com/（standard_user / secret_sauce），
> 把第一个商品加入购物车，验证数量为 1，最后生成 .robot 脚本。

AI 会依次调用：
1. `analyze_scenario` — 建会话
2. `open_persistent_browser` — 开持久化浏览器
3. `execute_step` — 逐条执行 Fill Text / Click / Get Text
4. `build_test_suite` — 产出 .robot

---

## 7. 核心工具参考

### 7.1 `open_persistent_browser`（4 种模式）

```python
# 模式 1：持久化（默认）—— profile 落盘，跨重启免登录
open_persistent_browser(session_id="s1", url="https://x.com")
# user_data_dir 默认 ~/.robotmcp/browser-profiles/<session_id>/

# 模式 2：复用已开浏览器（AI 手动开的浏览器，脚本接着用）
open_persistent_browser(session_id="s1", reuse_existing=True, url="https://x.com")

# 模式 3：全新隔离 profile（不保留任何状态）
open_persistent_browser(session_id="s1", fresh_profile=True, url="https://x.com")

# 模式 4：重置业务状态（保留 cookie，清 localStorage/sessionStorage）
open_persistent_browser(session_id="s1", clean_state=True, url="https://x.com")
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `user_data_dir` | `~/.robotmcp/browser-profiles/<session_id>/` | 持久化 profile 目录 |
| `url` | None | 打开后导航地址 |
| `headless` | True | 无头模式 |
| `browser` | chromium | chromium/firefox/webkit |
| `reuse_existing` | False | 复用 Browser 库已开浏览器 |
| `fresh_profile` | False | 临时全新 profile（忽略 user_data_dir） |
| `clean_state` | False | 清 localStorage/sessionStorage 后重新导航 |

> **注意**：若站点把登录态存在 localStorage/sessionStorage（如 saucedemo），
> `clean_state` 会连登录一起清，需重新登录。要连 cookie 一起清用 `fresh_profile`。

### 7.2 `execute_step`（含失败自愈）

```python
execute_step(keyword="Browser.Click", arguments=["id=login-button"], session_id="s1")
```

失败时自动：
1. 判断是否定位类错误（locator/timeout/no element 等）
2. 抓 filtered DOM
3. 规则生成候选定位器（`text=X` → `xpath=//*[contains(normalize-space(text()), "X")]`）
4. 规则全败 → 宿主支持 sampling 时让 LLM 生成定位器
5. 成功返回 `self_healed=True, self_healed_by=rule|llm`；全败附 `self_heal_dom` 摘要

### 7.3 `manage_session`（生命周期）

```python
manage_session(action="init", session_id="s1", libraries=["Browser"])
manage_session(action="start_test", session_id="s1", test_name="登录测试")
manage_session(action="set_suite_setup", session_id="s1", keyword="New Browser", args=["chromium"])
manage_session(action="close_session", session_id="s1")   # 显式关闭，真正释放浏览器进程
```

会话状态机：
- `active` — 调试中，超时不自动清理（keep-alive）
- `idle` — 超时降级，可被清理
- `closed` — 显式关闭，浏览器已释放

### 7.4 `build_test_suite`

```python
build_test_suite(test_name="Saucedemo 登录", session_id="s1")
```

只包含**执行验证过**的步骤，返回 `rf_text` 字段（.robot 内容）。

---

## 8. 环境变量

| 变量 | 说明 |
|---|---|
| `PLAYWRIGHT_BROWSERS_PATH` | Playwright 浏览器路径（见 4.3，**必设**） |
| `ROBOTMCP_LAZY_INIT` | `0` 关闭惰性初始化 |
| `ROBOTMCP_OUTPUT_MODE` | `auto`/`inline`，大输出是否外置为 artifact |
| `ROBOTMCP_FETCH_ARTIFACT` | `true` 时启用 artifact 拉取工具 |

---

## 9. 常见问题

### 9.1 `Executable doesn't exist ... chromium_headless_shell`
未设置 `PLAYWRIGHT_BROWSERS_PATH`。见 4.3。

### 9.2 `No page source available for this session`
session 的 `imported_libraries` 没有 Browser（通常是用 `open_persistent_browser`
直接建 session、没走 `analyze_scenario`）。本版本已在 `open_persistent_browser`
里自动登记 Browser，正常不会出现；若自建 session 请先 `manage_session(action="init", libraries=["Browser"])`。

### 9.3 生成的 .robot 重跑失败（元素状态漂移）
持久化 profile 保留了业务状态。用 `clean_state=True` 或跑前清状态：
```robotframework
Evaluate JavaScript    ${None}    () => { localStorage.clear(); sessionStorage.clear(); }
```

### 9.4 `profile 被占用`
旧浏览器没退出。本版本会自动清理 crash 残留的 SingletonLock；
若进程仍存活，先 `manage_session(action="close_session")` 或手动结束进程。

### 9.5 自愈没触发 LLM
`ctx.sample()` 需要宿主客户端支持 MCP sampling（Claude Desktop / Cursor 等）。
不支持的客户端会静默降级为规则版，返回结果带 `self_heal_error`。

---

## 10. 自测脚本

项目 `demo/` 目录下的验证脚本（需设 `PLAYWRIGHT_BROWSERS_PATH`）：

```bash
# P0：持久化浏览器 + 规则自愈
.venv/Scripts/python.exe demo/test_p0.py

# P1：生命周期状态机 + reuse_existing
.venv/Scripts/python.exe demo/test_p1.py
.venv/Scripts/python.exe demo/test_p1_release.py   # 浏览器进程释放 PID 验证

# P3：LLM 兜底自愈（FakeCtx）
.venv/Scripts/python.exe demo/test_p3.py

# P4：fresh_profile / clean_state
.venv/Scripts/python.exe demo/test_p4.py

# 真实 MCP 端到端
.venv/Scripts/python.exe demo/e2e_client.py
.venv/Scripts/python.exe demo/test_p1_e2e.py
.venv/Scripts/python.exe demo/test_p3_e2e.py
.venv/Scripts/python.exe demo/test_p4_e2e.py

# 实战：saucedemo 登录 + 购物车 + 生成 .robot
.venv/Scripts/python.exe demo/real_world_acceptance.py
```

---

## 11. 二次开发说明

### 源码结构（改动集中在 3 个文件）

| 文件 | 改动 |
|---|---|
| `src/robotmcp/server.py` | `open_persistent_browser`、`_self_heal_step`、`_llm_suggest_locator`、`_clean_browser_state`、`close_session` 分支 |
| `src/robotmcp/components/execution/session_manager.py` | `_release_rf_context`、`cleanup_expired_sessions` 状态机 |
| `src/robotmcp/components/execution/keyword_executor.py` | `new persistent context` 的 state 追踪 |
| `src/robotmcp/models/session_models.py` | `lifecycle_status` 字段 |
| `src/robotmcp/domains/shared/kernel.py` | `SessionAction` 加 `close_session` |

### 关键坑（改代码前务必知道）

1. **`end_suite()` 不关浏览器** —— 释放 session 必须先显式 `Close Browser`，再 `cleanup_context`。
2. **`New Persistent Context` 不含 `"new context"` 子串** —— `_extract_browser_state_updates` 需要单独分支，否则 `context_id` 不更新、复用检测失效。
3. **`open_persistent_browser` 直接建 session** —— 必须手动把 Browser 登记到 `imported_libraries`，否则 `get_page_source` 的 web 库自检直接返回空。
4. **持久化 profile 会污染业务状态** —— 提供 `clean_state` / `fresh_profile`。

更多细节见 `二次开发架构设计.md` 与 `demo/` 下的验证脚本。
