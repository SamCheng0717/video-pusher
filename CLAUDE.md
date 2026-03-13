# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 安装依赖
uv sync
uv run playwright install chromium   # 首次必须，约 150MB

# 运行所有测试
uv run pytest tests/ -v

# 运行单个测试文件
uv run pytest tests/test_vp_accounts.py -v

# 运行单个测试
uv run pytest tests/test_vp_accounts.py::test_format_tags -v
```

## Architecture

每个 skill 是一个独立目录，包含一个 Python 脚本和一个 SKILL.md：

```
skills/
  vp-accounts/          # 账号组管理（登录/查询/删除）
  vp-publish/           # 多平台编排（仅 SKILL.md，无脚本）
  vp-publish-douyin/    # 抖音
  vp-publish-xhs/       # 小红书
  vp-publish-shipinhao/ # 微信视频号
  vp-publish-threads/   # Threads
  vp-publish-ins/       # Instagram
```

**账号数据流：** `vp-accounts` 管理 `profile/accounts.json`，其中记录每个账号组各平台的 Chromium Profile 子路径（如 `douyin/group_0`）。发布脚本读取该文件定位 Profile 目录，加载已保存的登录 Session。

**发布脚本统一模式：**
1. 从 `accounts.json` 加载 profile 目录，清理 Singleton 锁文件
2. `launch_persistent_context` 加载已有 Session，`headless=False`
3. 整个浏览器操作包在 `try/except Exception: pass` 内
4. 自动填写表单；每步失败只打印警告，不中断流程
5. 结尾 `page.wait_for_event("close", timeout=0)` 等待用户关窗退出

## Key Technical Constraints

**`networkidle` 不可用：** 所有平台有持续后台请求导致永远不触发。统一用 `domcontentloaded` + `time.sleep(2)`。

**Mac 浏览器关闭：** Mac 点击 X 只关窗口不终止进程。必须用 `page.wait_for_event("close")` 而非 `context.wait_for_event("close")`。登录脚本同样适用，不能用长时间 `wait_for_selector` 阻塞在关闭之前。

**隐藏的 file input：** 所有平台的 `input[type="file"]` 是隐藏元素，必须用 `state="attached"` 而非默认 `state="visible"`。

**标签输入（抖音/小红书）：** 每个 `#标签` 输入后：`time.sleep(0.5)` → `Escape`（小红书还需再 `time.sleep(0.3)`）→ 空格，才能使标签生效并关闭自动补全。

**视频号字段：**
- 短标题：`input[placeholder*="概括视频主要内容"]`（独立字段，非拼入正文）
- 描述：`div[contenteditable]`（属性值为 `""` 不是 `"true"`）

**Threads：** 先填文字再上传媒体；打开发帖框用 `[aria-label="创建"]`（中文界面）。

**Instagram：** 创建帖子按钮 `[aria-label="新帖子"]`（中文界面）。

## Tests

`tests/test_vp_accounts.py` 覆盖纯逻辑函数（`load/save_accounts`、`format_tags`、`get_profile_subpath`）和 CLI 命令（`add/delete/list/status/remove`），用 `monkeypatch` 隔离文件系统。

`tests/test_publish_*.py` 只测 CLI 参数校验（必填项缺失时 exit != 0）和 `PROFILE_BASE` 路径正确性，不启动浏览器。
