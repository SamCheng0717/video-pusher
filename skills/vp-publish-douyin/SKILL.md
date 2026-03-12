---
name: vp-publish-douyin
description: Use when publishing video content to Douyin (抖音), requires a logged-in account group managed by vp-accounts
---

# vp-publish-douyin

## Overview

自动打开抖音创作者平台，上传视频并填写标题、正文、标签，等待用户确认发布。

## Usage

```bash
python skills/vp-publish-douyin/publish_douyin.py \
  --file /path/to/video.mp4 \
  --title "标题（必填）" \
  --description "正文内容" \
  --tags "医美 玻尿酸 韩国整形" \
  --group "A组"
```

**参数说明：**
- `--file`：视频文件路径（mp4/mov/avi），必填
- `--title`：标题，填入独立标题输入框，必填
- `--description`：正文内容，选填
- `--tags`：标签，空格分隔，自动添加 `#` 前缀，选填
- `--group`：账号组名称，必须已通过 vp-accounts 完成登录

## Prerequisites

账号组必须已登录抖音：
```bash
python skills/vp-accounts/vp_accounts.py status "A组" douyin
# exit 0 = 已登录，可发布
# exit 1 = 未登录，先执行 login
```

## Flow

1. 浏览器打开抖音创作者平台
2. 自动上传视频（等待约 8 秒处理）
3. 自动填写标题和正文
4. **用户检查内容后手动点击【发布】按钮**
5. 在终端按回车关闭浏览器
