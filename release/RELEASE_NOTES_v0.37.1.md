# auto_rf v0.37.1

Windows MCP stdio 浏览器启动与生命周期稳定性修复。保留上游 Apache-2.0 LICENSE 和 NOTICE。

## 修复

- 删除启动时无条件创建浏览器和 `__warm__` 会话的预热。
- 通过线程堆栈确认首次 Browser 调用卡在 gRPC Health；Node 继承 MCP stdin 导致启动阻塞。仅隔离 Browser 模块的 Popen/run stdin 为 DEVNULL，真实 MCP 不再需要浏览器预热。
- 会话关闭使用创建/执行关键字的 RF 单线程 executor，关闭全部浏览器后释放上下文；服务退出时显式关闭 executor。
- 多个会话引用同一 RF 上下文时，仅最后一个引用关闭才 end_suite，避免剩余会话报 Cannot access execution context。
- example.com 与 Saucedemo 验收增加实际内容断言、生成脚本检查、关闭检查，并独立调用 Robot 执行生成的脚本。兼容 MCP 返回对象的 isError/is_error 字段；失败检查在 Python 优化模式下仍有效。
- 增加限时验收入口，保留退出码，超时返回 124 并清理本次运行的进程树。修复 P4 等待多个元素及遗漏结果断言；PID 检查只跟踪本次测试的 Chromium。

## 已验证

环境：Windows 11 / Python 3.14.7 / Browser 21.0.0 / 匹配的系统 Chromium 缓存。未重新下载或删除浏览器缓存。

- 11 个相关单元测试文件：154 passed、5 skipped；1 条既有 TestSuite 类收集提示。
- P0：持久化复用；不可修复定位器明确失败，同时返回 DOM 和规则重试证据。
- P1：active→idle→移除、活动恢复、显式关闭与复用参数。PID 验证观察到实际 Chromium 创建，关闭后对应 PID 全部退出。
- P3：FakeCtx sampling 控制流和真实浏览器重试成功；未测试真实模型服务。
- P4：全新 profile、清除 storage 后重新登录、6 个商品与恢复后的加购按钮数量断言。
- 真实 MCP example.com 标题、URL、链接数量断言；生成 .robot 后独立 Robot 执行 1/1 PASS。
- 真实 MCP Saucedemo 登录、Products 标题、购物车数量 1 断言；生成 .robot 后独立 Robot 执行 1/1 PASS。
- 独立新 venv 从 wheel 安装，确认 robotmcp 来自 site-packages；FastMCP 4.1.6、Browser 21.0.0 下重复真实 MCP 与独立 Robot 链路。
- 初始化 MCP 后没有 Node/Chromium；验收运行结束后，跟踪的子进程无存活残留。限时入口实际触发并返回 124。
- uv build 生成 wheel 与 sdist。此次验证为针对性回归，未运行整个上游测试集。

## 使用

```bash
uv pip install 'rf_mcp_enhanced-0.37.1-py3-none-any.whl[web]'
python -m Browser.entry init --skip-browsers
# 设置 PLAYWRIGHT_BROWSERS_PATH 为已安装且版本匹配的缓存目录
python demo/run_acceptance.py quick_acceptance --timeout 120
python demo/run_acceptance.py real_world_acceptance --timeout 120
```

## 已知限制

- RF/Browser 状态仍在同一进程中共享，多个浏览器会话尚未隔离；关闭一个会话可能影响其他会话。需要隔离时使用独立 server 进程。
- reuse_existing 仅针对当前 Browser 库管理的浏览器，不接管任意手工 Chrome。
- 同步第三方关键字无法由 asyncio 取消强制终止，外层验收进程超时并非服务端任意关键字硬超时保证。
- fresh_profile 临时目录仍需自行清理；Node driver 允许存活到 server 退出。
- sampling 依赖宿主支持；P3 使用固定响应替身，不代表真实模型质量验证。
- 此次未验证其他系统和 Browser 版本；Browser 21 要求 Python 3.11+，核心包要求 Python 3.10+。
