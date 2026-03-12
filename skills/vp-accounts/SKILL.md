---
name: vp-accounts
description: Use when managing multi-platform video publisher account groups, checking login status for douyin/xhs/shipinhao/threads/instagram, creating or deleting account groups, or initiating browser-based login to save platform sessions
---

# vp-accounts

## Overview

管理视频发布平台的账号组和登录状态。登录一次，Session 永久保存，发布时自动复用。

## Commands

```bash
# 查看所有账号组及各平台登录状态
python skills/vp-accounts/vp_accounts.py list

# 创建账号组
python skills/vp-accounts/vp_accounts.py add "A组"

# 删除账号组
python skills/vp-accounts/vp_accounts.py delete "A组"

# 登录某平台（打开浏览器，用户手动登录后关闭窗口）
python skills/vp-accounts/vp_accounts.py login "A组" douyin
# platform 可选：douyin | xhs | shipinhao | threads | ins

# 检查登录状态（exit 0=已登录，exit 1=未登录）
python skills/vp-accounts/vp_accounts.py status "A组" douyin
```

## Workflow

1. 首次使用先创建账号组：`add "组名"`
2. 对每个平台执行 `login "组名" <platform>`，浏览器打开后登录，关闭窗口即保存
3. 用 `list` 确认各平台显示 `true`
4. 之后发布时 Session 自动复用，无需重复登录

## Storage

- 账号组配置：`profile/accounts.json`
- Chromium Session：`profile/<platform>/group_<N>/`
- `profile/` 目录已加入 `.gitignore`，不会提交到 Git

## Install

```bash
uv sync
uv run playwright install chromium
```
