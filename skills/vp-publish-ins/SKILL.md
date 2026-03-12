---
name: vp-publish-ins
description: Use when publishing photo or video content to Instagram, requires a logged-in account group managed by vp-accounts
---

# vp-publish-ins

## Overview

自动打开 Instagram，上传图片/视频，通过多步骤流程（裁剪→滤镜→Caption）完成发布。支持纯文字发布。

## Usage

```bash
python skills/vp-publish-ins/publish_ins.py \
  --file /path/to/photo.jpg \
  --title "Caption 内容（必填）" \
  --tags "医美 玻尿酸" \
  --group "A组"
```

**注意：** Instagram 发布流程为多步骤，上传后需依次点击"下一步"直到 Caption 页，脚本自动完成点击。
