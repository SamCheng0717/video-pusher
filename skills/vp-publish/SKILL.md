---
name: vp-publish
description: Use when publishing video or content to multiple platforms at once, orchestrates vp-accounts status check and calls platform-specific publish skills in sequence
---

# vp-publish

## Overview

一键发布到多平台的编排入口。Claude 负责协调：检查登录状态、按顺序调用各平台发布脚本、处理未登录情况。

## Usage

告诉 Claude：
> "发布 /path/to/video.mp4 到抖音和小红书，使用 A组 账号，标题是 xxx，正文是 yyy，标签是 医美 玻尿酸"

Claude 会：
1. 检查 A组 在抖音、小红书的登录状态
2. 如有平台未登录，询问是先登录还是跳过
3. 依次调用各平台发布脚本

## Workflow

```
1. 确认参数（文件路径、标题、正文、标签、账号组、目标平台）

2. 对每个目标平台检查登录：
   python skills/vp-accounts/vp_accounts.py status "A组" douyin
   # exit 0 = 已登录，继续；exit 1 = 询问用户

3. 已登录平台依次发布：
   python skills/vp-publish-douyin/publish_douyin.py \
     --file <path> --title <title> --description <desc> \
     --tags <tags> --group <group>
   # 等用户在浏览器发布完成、终端按回车后，再发布下一个平台

4. 汇报所有平台发布结果
```

## Supported Platforms

| 平台 | skill | 文件必填 |
|------|-------|---------|
| 抖音 | vp-publish-douyin | 是 |
| 小红书 | vp-publish-xhs | 是 |
| 视频号 | vp-publish-shipinhao | 是 |
| Threads | vp-publish-threads | 否 |
| Instagram | vp-publish-ins | 否 |

## Prerequisites

```bash
uv sync
uv run playwright install chromium
# 各平台完成登录：
python skills/vp-accounts/vp_accounts.py login "A组" douyin
```
