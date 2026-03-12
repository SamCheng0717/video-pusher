---
name: vp-publish-xhs
description: Use when publishing video or image content to Xiaohongshu (小红书/XHS), requires a logged-in account group managed by vp-accounts
---

# vp-publish-xhs

## Overview

自动打开小红书创作者平台，上传视频/图片并填写标题、正文、标签，等待用户确认发布。

**注意：** 发布视频时会自动切换到视频发布模式（点击"发布视频"按钮）。

## Usage

```bash
python skills/vp-publish-xhs/publish_xhs.py \
  --file /path/to/content.mp4 \
  --title "标题（必填）" \
  --description "正文" \
  --tags "医美 玻尿酸" \
  --group "A组"
```

**`--file`** 支持视频（mp4/mov/avi/mkv）和图片（jpg/png/gif）。
