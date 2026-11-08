# auto_rf v0.37.0 — rf-mcp 增强版

基于 [rf-mcp v0.36.0](https://github.com/manykarim/rf-mcp) 的二次开发，遵循 Apache-2.0。

核心解决：**AI 写自动化时反复打开浏览器调试、效率低**。

## 核心增强

### 1. 持久化浏览器 `open_persistent_browser`
- `New Persistent Context`：profile 落盘，跨 server 重启免登录
- 自动清理 crash 残留的 SingletonLock
- 4 种模式：持久化（默认）/ `reuse_existing` / `fresh_profile` / `clean_state`

### 2. 失败自愈
- **规则版**：`text=X` → `xpath=//*[contains(normalize-space(text()), "X")]` 等候选重试
- **LLM 兜底**：规则全败时回退宿主 sampling（`ctx.sample`）生成定位器
- 结果标记 `self_healed_by=rule|llm`

### 3. 会话生命周期
- 状态机：`active`（keep-alive）/ `idle` / `closed`
- `manage_session(action="close_session")` 显式关闭，**真正释放 Playwright 进程**（PID 实测）

## 修复
- **Browser 库登记**：`open_persistent_browser` 直接建 session 时登记 Browser，避免 DOM 抓取自检失败导致自愈失效
- **`end_suite()` 不关浏览器**：释放 session 前显式 `Close Browser`，否则 Playwright 进程残留

## 安装

从 release 附件安装（推荐）：

```bash
uv pip install "rf-mcp-enhanced[web] @ https://github.com/gsk74521/auto_rf/releases/download/v0.37.0/rf_mcp_enhanced-0.37.0-py3-none-any.whl"
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium
```

从源码安装：

```bash
git clone https://github.com/gsk74521/auto_rf.git
cd auto_rf
uv sync --extra all
```

> 注意：robotframework-browser 需要版本匹配的浏览器，装完必须跑
> `python -m Browser.entry install chromium`，否则报 `Executable doesn't exist`。

## 文档
- [USAGE_ZH.md](https://github.com/gsk74521/auto_rf/blob/main/USAGE_ZH.md) — 使用说明
- [PUBLISH_ZH.md](https://github.com/gsk74521/auto_rf/blob/main/PUBLISH_ZH.md) — 打包发布
- [二次开发架构设计.md](https://github.com/gsk74521/auto_rf/blob/main/二次开发架构设计.md) — 架构与改造点

## 验证
- P0 / P1 / P3 / P4 验收测试全部通过
- 真实 MCP 端到端（saucedemo 登录 + 购物车 + 生成 .robot）通过
- 干净 venv 从 wheel 安装 + `robotmcp --version` = 0.37.0 通过

## 许可
本项目是 rf-mcp 的衍生作品，遵循 **Apache License 2.0**。
原始版权与许可声明保留，详见仓库 `LICENSE` 与 `NOTICE`。
