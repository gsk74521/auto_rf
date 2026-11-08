# 发布说明（供其他人使用）

> 本文件说明如何把增强版打包、分发给他人。

---

## 1. 发布产物

`uv build` 后在 `dist/`（正式产物整理到 `release/`）生成：

| 文件 | 用途 |
|---|---|
| `release/rf_mcp_enhanced-0.37.0-py3-none-any.whl` | wheel，`pip install` 用 |
| `release/rf_mcp_enhanced-0.37.0.tar.gz` | sdist，源码安装用 |

> 当前正式产物已放在 `release/` 目录（`dist/` 在 Windows 上可能被文件锁占用）。
> 校验和：
> - whl: `9084616cf7f400ee05af1fb396aa57c0fc475f8524c99655b39bf64ac2ab5978`
> - tar.gz: `32fbcf24d050009395fb08ec8476a401df516073d5bd7f429654374099127240`

**包名 `rf-mcp-enhanced`**，与上游 PyPI 的 `rf-mcp` 不冲突。
**import 路径仍是 `robotmcp`，命令仍是 `robotmcp` / `rf-mcp`**，使用方式完全不变。

---

## 2. 安装方式（按分发渠道选一种）

### 2.1 本地 wheel / 共享盘（最简单，无需账号）

```bash
uv pip install rf_mcp_enhanced-0.37.0-py3-none-any.whl
# 或
pip install rf_mcp_enhanced-0.37.0-py3-none-any.whl
```

然后初始化 node wrapper + 下载匹配浏览器：
```bash
python -m Browser.entry init --skip-browsers
python -m Browser.entry install chromium   # 下载匹配版本的 Playwright 浏览器
```

> 若复用系统已装浏览器，设 `PLAYWRIGHT_BROWSERS_PATH`（见 USAGE_ZH.md 4.3）。

### 2.2 内网私服（公司内部 PyPI / Nexus / Artifactory）

```bash
uv publish --publish-url https://your-pypi/simple/ --token <TOKEN> dist/*
# 使用者：
uv pip install --index-url https://your-pypi/simple rf-mcp-enhanced
```

### 2.3 公共 PyPI（需账号 + API Token）

```bash
# 1) 注册 PyPI 账号，创建 API token
# 2) 上传（uv 0.11+ 自带 publish）
uv publish --token pypi-<你的token> dist/rf_mcp_enhanced-0.37.0-py3-none-any.whl dist/rf_mcp_enhanced-0.37.0.tar.gz

# 或使用 twine
pip install twine
twine upload dist/*
```

> 上传前先 `uv build`，并确认版本号递增（见第 4 节）。

### 2.4 GitHub Release / git 直接安装

```bash
# 当前目录不是 git 仓库，先初始化：
git init
git add -A
git commit -m "rf-mcp-enhanced 0.37.0"
git remote add origin https://github.com/<你>/rf-mcp-enhanced.git
git push -u origin main

# 使用者从 git 安装：
uv pip install "git+https://github.com/<你>/rf-mcp-enhanced.git"
```

GitHub Release 里上传 `dist/` 的两个文件，别人可直接下载 wheel 安装。

---

## 3. 重新打包（改了代码之后）

```bash
cd F:/github/auto_robot
# 1) 改 pyproject.toml 的 version（必须递增）
# 2) 打包
uv build
# 3) 产物在 dist/
```

> `uv build` 只读取 `pyproject.toml`，不需要重新 `uv sync`。

---

## 4. 版本管理建议

| 场景 | 版本号 |
|---|---|
| 当前增强版首发 | `0.37.0` |
| 修 bug | `0.37.1` |
| 加功能 | `0.38.0` |
| 跟随上游升级 | 同步上游主版本 + 增强补丁号 |

> 版本号必须严格递增，否则 PyPI 拒绝上传、pip 不会升级。

---

## 5. 依赖与 extras

wheel 默认只装核心依赖（fastmcp / robotframework / pydantic 等）。
**浏览器测试必须装 `web` extra：**

```bash
# 从 wheel 安装时指定 extras
uv pip install "rf-mcp-enhanced[web] @ file:///F:/github/auto_robot/dist/rf_mcp_enhanced-0.37.0-py3-none-any.whl"

# 或装全部
uv pip install "rf-mcp-enhanced[all] @ file:///..."
```

extra 对应：

| extra | 内容 |
|---|---|
| `web` | robotframework-browser + seleniumlibrary（推荐，本增强版主要面向 browser） |
| `api` | robotframework-requests |
| `mobile` | robotframework-appiumlibrary |
| `database` | robotframework-databaselibrary |
| `memory` | sqlite-vec + model2vec（自愈记忆） |
| `all` | 以上全部（不含 desktop 预发布） |

> 注：上游 `pyproject.toml` 里 `web` extra 是 `robotframework-browser + seleniumlibrary`；
> `browser` 不在上游定义里，安装时用 `web` 或 `all`。
> 若需要精简，可自行在 pyproject.toml 增加 `browser = ["robotframework-browser"]`。

---

## 6. 合规

- 本项目是 **[rf-mcp](https://github.com/manykarim/rf-mcp) 的二次开发**，遵循上游 **Apache-2.0** 许可。
- `LICENSE` 与上游版权声明必须保留。
- 发布时建议在 README 顶部注明「Based on rf-mcp v0.36.0」并附上游链接。

---

## 7. 发布前检查清单

- [ ] `pyproject.toml` 的 version 已递增
- [ ] `uv build` 成功，`dist/` 有 wheel + sdist
- [ ] wheel 里包含改动文件（`robotmcp/server.py` 等）
- [ ] `uv pip install --target /tmp/t --no-deps dist/*.whl` 能装
- [ ] 在干净环境 `uv pip install "rf-mcp-enhanced[web]"` 后 `robotmcp --version` 正常
- [ ] `USAGE_ZH.md` 随包或随 Release 一起提供
