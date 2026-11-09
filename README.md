# auto_rf · Robot Framework MCP 增强版

**简体中文** | [English](README_EN.md)

> **Based on [rf-mcp v0.36.0](https://github.com/manykarim/rf-mcp)，原作者 Many Kasiriha。**
> 本项目为二次开发，遵循上游 [Apache-2.0 许可](LICENSE)，保留上游版权声明。修改说明见 [NOTICE](NOTICE)。

让 AI 逐步编写和调试自动化，在失败时保留浏览器状态、检查 DOM 并续跑，最终输出可独立执行的 Robot Framework `.robot` 脚本。

`auto_rf` 是一个 MCP Server。Python 分发包名为 **`rf-mcp-enhanced`**，导入模块仍为 `robotmcp`，命令仍为 `robotmcp` / `rf-mcp`。

[下载 v0.37.1](https://github.com/gsk74521/auto_rf/releases/tag/v0.37.1) · [完整使用说明](USAGE_ZH.md) · [打包发布说明](PUBLISH_ZH.md)

## 工作方式

不必每次生成整份脚本、运行失败后又从头打开浏览器。AI 在同一个服务进程和会话中逐条验证关键字，遇到问题检查当前 DOM，修复后继续执行，最后生成脚本并独立验证。

```text
analyze_scenario → 发现关键字 → open_persistent_browser
                → execute_step → 当前页面抓 DOM / 修复 / 重试
                → build_test_suite → 保存 .robot → Robot Framework 独立执行
```

## 相比上游的增强

| 能力 | 行为 |
| --- | --- |
| 持久化浏览器 | 同一会话复用浏览器上下文，profile 落盘；能否保留登录取决于站点的存储和过期规则。 |
| 定位器自愈 | 定位失败后获取 DOM、尝试规则候选；宿主支持 sampling 时可请求 LLM 提供候选。不能保证自动修复成功。 |
| 生命周期管理 | 跟踪 active/idle/closed 状态，提供 `close_session` 显式关闭。 |
| 浏览器复用 | 向 Browser 库透传 `reuse_existing`，复用该库管理的浏览器。 |
| 状态控制 | 支持全新 profile，或保留 cookie、清理 localStorage/sessionStorage。 |
| Windows stdio 稳定性 | v0.37.1 隔离 Browser 子进程 stdin，删除启动预热浏览器，RF 执行和释放使用专用工作线程。 |

保留上游的关键字发现、套件生成及可选的 Web/API/移动端/数据库等集成。继承工具见 [工具参考](docs/MCP_TOOLS.md)，增强版行为以本 README 和 [USAGE_ZH.md](USAGE_ZH.md) 为准。

## 环境要求

- 使用 Browser 21 时推荐 **Python 3.11+**；核心包要求 Python 3.10+。
- Node.js LTS，用于 Browser 库的 Node wrapper。
- 与已安装 Browser 库版本匹配的浏览器二进制。
- 支持 MCP 的 AI 客户端；仅 LLM 自愈需要宿主支持 sampling。
- 推荐使用 [uv](https://docs.astral.sh/uv/) 管理环境。

本次发布实测环境为 Windows 11、Python 3.14、Browser 21.0.0。其他系统和 Browser 版本未在此次发布中实测。

## 从源码安装

```bash
git clone https://github.com/gsk74521/auto_rf.git
cd auto_rf
uv sync --extra web
```

激活环境，让后续命令使用项目中的 Python：

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
# Windows Git Bash 则使用：source .venv/Scripts/activate
```

初始化 Node wrapper，再安装 Chromium：

```bash
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium
```

其他可选依赖有 `api`、`mobile`、`database`、`frontend`、`memory`。`uv sync --extra all` 安装组合依赖，但不包含 `desktop` 和 `semantic`。

## 从 Release wheel 安装

从 [Releases](https://github.com/gsk74521/auto_rf/releases) 下载 wheel，在空目录建立环境：

```bash
uv venv --python 3.11
# 按上文激活当前环境，然后执行：
uv pip install "./rf_mcp_enhanced-0.37.1-py3-none-any.whl[web]"
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium
robotmcp --version
```

`[web]` 会安装 Browser 和 Selenium 库，裸 wheel 不含这些可选依赖。本增强版使用源码或 Release 附件安装；`pip install rf-mcp` 安装的是上游项目。

### 浏览器缓存与国内镜像

要复用已有缓存，在**安装浏览器和启动服务之前**设置路径，且缓存版本必须匹配。实测 Browser 21.0.0 使用 Chromium revision 1248。

```powershell
# Windows PowerShell
$env:PLAYWRIGHT_BROWSERS_PATH = "$env:LOCALAPPDATA/ms-playwright"
# 可选：国内下载镜像
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://registry.npmmirror.com/-/binary/playwright"
python -m Browser.entry install chromium
```

```bash
# Windows Git Bash
export PLAYWRIGHT_BROWSERS_PATH="$LOCALAPPDATA/ms-playwright"
export PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright
python -m Browser.entry install chromium
```

镜像是否有对应文件取决于浏览器版本；遇到 404，取消 `PLAYWRIGHT_DOWNLOAD_HOST` 后改用官方源。`Executable doesn't exist` 通常表示缓存路径或浏览器版本不匹配。需要并存不同 Browser 版本时，建议使用不同缓存目录。

## 配置 MCP 客户端

使用**安装了本增强版的 Python 解释器绝对路径**。下面是 Windows 源码环境示例，请替换所有示例路径：

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

Linux/macOS 通常使用 `/absolute/path/auto_rf/.venv/bin/python`。不同客户端的配置结构不同，上例采用 `mcpServers`。如果使用 Browser 默认下载目录，可省略自定义缓存环境变量。项目自定义 RF 库也需安装在服务所用的 Python 环境中。

需要手动启动时运行 `python -m robotmcp.server`。默认使用 stdio，stdout 专用于 MCP 协议消息。

## 给 AI 的使用示例

```text
使用 robotmcp 和 Browser 库访问 https://www.saucedemo.com/。
用 standard_user / secret_sauce 登录，将第一个商品加入购物车，断言数量为 1。
执行前先发现关键字；整个调试过程使用同一个 session_id 和浏览器。
失败时获取当前 DOM，修复并重试失败步骤。
所有步骤通过后生成 .robot，保存文件，再用 Robot Framework 独立执行。
完成后显式关闭会话。
```

## 浏览器模式

以下展示 MCP 工具参数，不是可直接运行的 Python 程序：

```python
# 默认持久化 profile；可见浏览器便于调试
open_persistent_browser(session_id="s1", url="https://example.com/", headless=False)
# 复用当前 Browser 库管理的浏览器
open_persistent_browser(session_id="s1", reuse_existing=True)
# 使用临时全新 profile
open_persistent_browser(session_id="s2", fresh_profile=True, url="https://example.com/")
# 打开时清 localStorage/sessionStorage，保留 cookie
open_persistent_browser(session_id="s3", clean_state=True, url="https://example.com/")
# 显式关闭
manage_session(action="close_session", session_id="s1")
```

- 后续步骤保持相同 `session_id`。默认 profile 为 `~/.robotmcp/browser-profiles/<session_id>/`，可通过 `user_data_dir` 指定目录。
- 默认 `headless=True`；可见调试使用 `headless=False`。
- 持久化上下文已经打开时直接返回 `reused=True`，这条路径不会应用新 URL、profile 或清理参数。导航请调用 `execute_step`；更换 profile 或清理状态请关闭后重新打开。
- `clean_state` 会清除存放在 localStorage/sessionStorage 的登录态。`fresh_profile` 也不带旧 cookie，临时目录目前需自行清理。
- `reuse_existing` 不接管任意手工打开的 Chrome。
- `build_test_suite` 返回 `rf_text`，需保存为 `.robot`。只读检查步骤可能不被记录，可用 `record=True` 或 `assign_to` 明确记录；生成套件应包含断言，并独立执行验证。

## 验收

在**源码仓库**中，激活环境并准备匹配浏览器后运行：

```bash
python demo/run_acceptance.py quick_acceptance --timeout 120
python demo/run_acceptance.py real_world_acceptance --timeout 120
```

两者均通过真实 MCP stdio 执行，断言实际值，生成脚本，再由独立 Robot 进程重放。外层入口保留非零退出码；超时返回 **124**，终止本次进程树。验收脚本位于仓库，不随 wheel 安装。

v0.37.1 针对性回归结果为 **154 passed / 5 skipped**，P0/P1/P3/P4 通过。新环境安装发布 wheel 后，example.com 和 SauceDemo 均完成真实 MCP 链路，生成脚本各自独立执行 **1/1 PASS**，并检查了启动不打开浏览器和进程释放。此次未运行整个上游测试集。

## 当前限制

- 同进程 RF/Browser 状态共享，**多浏览器会话尚未隔离**，关闭一个会话可能影响其他会话。需要隔离时使用不同 MCP Server 进程。
- profile 保存状态，不保证服务重启后恢复原有标签页；能否保持登录取决于网站。
- sampling 依赖宿主支持；P3 使用固定响应替身验证控制流，未评估真实模型修复质量。
- 取消 asyncio 等待不能强制终止同步第三方关键字。验收进程超时不等于服务端所有关键字都有硬超时保证。
- Chromium 关闭后，Browser Node driver 可以存活到服务退出。

## 文档与许可

| 文档 | 内容 |
| --- | --- |
| [English README](README_EN.md) | 英文快速开始 |
| [完整使用说明](USAGE_ZH.md) | 工具参数、模式和常见问题 |
| [二次开发架构设计](二次开发架构设计.md) | 设计与开发说明 |
| [打包发布说明](PUBLISH_ZH.md) | 安装分发与版本发布 |
| [v0.37.1 发布说明](release/RELEASE_NOTES_v0.37.1.md) | 修复与验证范围 |
| [工具参考](docs/MCP_TOOLS.md) / [配置](docs/CONFIGURATION.md) / [示例](docs/EXAMPLES.md) | 继承的上游能力；其中上游安装示例需按本增强版调整 |

本项目遵循 **Apache-2.0**。再分发时保留 [LICENSE](LICENSE)、上游版权声明和 [NOTICE](NOTICE)。上游项目：[manykarim/rf-mcp](https://github.com/manykarim/rf-mcp)。
