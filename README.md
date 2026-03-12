# Video Pusher Skills

一组 Claude Code / OpenClaw skills，将视频/图文内容一键发布到多个社交平台。

支持平台：**抖音、小红书、微信视频号、Threads、Instagram**

## 安装

### Claude Code

```bash
# 克隆仓库到项目的 skills 目录
git clone https://github.com/your-username/video-pusher skills/video-pusher

# 或直接克隆到工作目录后使用
git clone https://github.com/your-username/video-pusher
cd video-pusher
```

安装 Python 依赖：

```bash
uv sync
```

> **首次使用必须运行：**
> ```bash
> uv run playwright install chromium
> ```
> 这会下载 Chromium 内核（约 150MB），只需执行一次。

### OpenClaw / ClawHub

```bash
# 安装全部 skills
clawhub install your-username/video-pusher

# 或单独安装某个 skill
clawhub install your-username/vp-accounts
clawhub install your-username/vp-publish
```

安装后同样需要安装 Chromium：

```bash
uv run playwright install chromium
```

## Skills

| Skill | 功能 |
|-------|------|
| `vp-accounts` | 管理账号组，登录/查询各平台登录状态 |
| `vp-publish` | 多平台编排入口，一次发布到多个平台 |
| `vp-publish-douyin` | 发布到抖音 |
| `vp-publish-xhs` | 发布到小红书 |
| `vp-publish-shipinhao` | 发布到微信视频号 |
| `vp-publish-threads` | 发布到 Threads（支持纯文字） |
| `vp-publish-ins` | 发布到 Instagram |

## 快速开始

### 1. 创建账号组

```bash
uv run python skills/vp-accounts/vp_accounts.py add "A组"
```

### 2. 登录各平台

```bash
# 浏览器打开登录页，完成登录后关闭窗口即自动保存
uv run python skills/vp-accounts/vp_accounts.py login "A组" douyin
uv run python skills/vp-accounts/vp_accounts.py login "A组" xhs
uv run python skills/vp-accounts/vp_accounts.py login "A组" shipinhao
uv run python skills/vp-accounts/vp_accounts.py login "A组" threads
uv run python skills/vp-accounts/vp_accounts.py login "A组" ins
```

### 3. 确认登录状态

```bash
uv run python skills/vp-accounts/vp_accounts.py list
```

### 4. 发布内容

```bash
# 发布到抖音
uv run python skills/vp-publish-douyin/publish_douyin.py \
  --file /path/to/video.mp4 \
  --title "标题" \
  --description "正文" \
  --tags "医美 玻尿酸" \
  --group "A组"

# 发布到小红书（视频自动切换到视频模式）
uv run python skills/vp-publish-xhs/publish_xhs.py \
  --file /path/to/video.mp4 \
  --title "标题" \
  --group "A组"

# 发布到视频号（无独立标题字段，标题拼入正文开头）
uv run python skills/vp-publish-shipinhao/publish_shipinhao.py \
  --file /path/to/video.mp4 \
  --title "标题" \
  --group "A组"

# 发布到 Threads（--file 可选，支持纯文字）
uv run python skills/vp-publish-threads/publish_threads.py \
  --title "正文内容" \
  --tags "医美 玻尿酸" \
  --group "A组"

# 发布到 Instagram
uv run python skills/vp-publish-ins/publish_ins.py \
  --file /path/to/photo.jpg \
  --title "Caption 内容" \
  --group "A组"
```

### 使用 Claude 一键多平台发布

告诉 Claude：

> 发布 `/path/to/video.mp4` 到抖音和小红书，使用 A组 账号，标题是「xxx」，正文是「yyy」，标签是 医美 玻尿酸

Claude 会自动检查登录状态，依次打开各平台浏览器完成发布。

## 工作原理

每个发布脚本会：
1. 打开 Chromium 浏览器，加载已保存的登录 Session
2. 自动填写标题、正文、标签并上传文件
3. **等待用户检查内容后手动点击发布按钮**
4. 用户在终端按回车关闭浏览器

登录 Session 保存在 `profile/` 目录（已加入 `.gitignore`）。

## 参数说明

所有发布脚本共用以下参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--file` | 视频号/抖音/小红书必填 | 媒体文件路径 |
| `--title` | 必填 | 标题（视频号拼入正文开头） |
| `--description` | 否 | 正文内容 |
| `--tags` | 否 | 标签，空格分隔，自动加 `#` |
| `--group` | 必填 | 账号组名称 |

## 目录结构

```
video-pusher/
├── skills/
│   ├── vp-accounts/          # 账号管理
│   ├── vp-publish/           # 多平台编排
│   ├── vp-publish-douyin/    # 抖音
│   ├── vp-publish-xhs/       # 小红书
│   ├── vp-publish-shipinhao/ # 视频号
│   ├── vp-publish-threads/   # Threads
│   └── vp-publish-ins/       # Instagram
├── tests/                    # 单元测试
├── profile/                  # Chromium Session（gitignored）
├── pyproject.toml
└── uv.lock
```

## 开发

```bash
# 运行测试
uv run pytest tests/ -v
```
