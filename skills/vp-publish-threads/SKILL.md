---
name: vp-publish-threads
description: Use when publishing text or media content to Threads, requires a logged-in account group managed by vp-accounts
---

# vp-publish-threads

## Overview

自动打开 Threads，填写文案并可选上传图片/视频，等待用户确认发布。支持纯文字发布。

## Usage

```bash
# 纯文字发布
python skills/vp-publish-threads/publish_threads.py \
  --title "正文内容（必填）" \
  --group "A组"

# 带媒体发布
python skills/vp-publish-threads/publish_threads.py \
  --file /path/to/media.mp4 \
  --title "正文内容" \
  --tags "医美 玻尿酸" \
  --group "A组"
```

**注意：** Threads 无标题字段，`--title` 内容作为帖子正文开头。
