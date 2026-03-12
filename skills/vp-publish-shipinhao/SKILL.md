---
name: vp-publish-shipinhao
description: Use when publishing video content to WeChat Channels (视频号/Shipinhao), requires a logged-in account group managed by vp-accounts
---

# vp-publish-shipinhao

## Overview

自动打开微信视频号创作平台，上传视频并填写内容，等待用户确认发布。

**注意：** 视频号无独立标题字段，标题会拼接在正文开头。登录需要微信扫码。

## Usage

```bash
python skills/vp-publish-shipinhao/publish_shipinhao.py \
  --file /path/to/video.mp4 \
  --title "标题（拼入正文开头）" \
  --description "正文" \
  --tags "医美 玻尿酸" \
  --group "A组"
```
