# Changelog

All notable changes to this project will be documented in this file.

---

## [1.2.0] - 2026-03-16

### Added
- **PEP 723 内联依赖声明**：所有 6 个 Python 脚本顶部添加 `# /// script` 元数据块，`uv run script.py` 无需 `uv sync` 即可自动安装 `playwright`，支持 ClawHub 等无 `uv.lock` 环境
- **CLAUDE.md**：新增项目指导文件，涵盖命令、架构概览、关键技术约束，供 Claude Code 开箱即用
- **双语 README**：完整重写为中英双语，加入 SEO 关键词、自然语言指令示例表格
- **自然语言示例**：README 顶部展示 4 条典型 AI 指令示例（查看状态 / 创建账号组 / 登录 / 发布）

### Changed
- README 中 GitHub 地址更新为 `SamCheng0717/video-pusher`
- 所有 SKILL.md 补充 `metadata.openclaw`（emoji、os、install）字段，适配 ClawHub 安装规范
- `.gitignore` 增加 `uv.lock` 排除项

---

## [1.1.0] - 2026-03

### Fixed
- **Mac 浏览器关闭检测**：将所有脚本的 `context.wait_for_event("close")` 改为 `page.wait_for_event("close", timeout=0)`，解决 Mac 点击 X 无法退出脚本的问题
- **networkidle 永久挂起**：所有平台改用 `domcontentloaded` + `time.sleep(2)`，消除因持续后台请求导致的 30 秒超时
- **隐藏 file input**：文件上传选择器统一加 `state="attached"`，解决上传无响应问题
- **登录脚本卡死**：移除 XHS / 视频号登录中 294 秒 `wait_for_selector` 阻塞，改为 3 秒快速探测 + `page.wait_for_event("close")`
- **抖音标签自动补全**：每个 `#标签` 输入后加 `Escape` 关闭下拉框再输空格，标签确认生效
- **小红书标签**：`Escape` 后追加 `time.sleep(0.3)` 再输空格，确保标签正常生效

### Changed (Threads)
- 完全重写 `publish_threads.py`：先点击「创建」按钮打开发帖框，先填文字再上传媒体，与其他平台流程对齐
- 发帖框触发改用 `[aria-label="创建"]`（中文界面），兼容多语言 fallback

### Changed (WeChat Channels / 视频号)
- 短标题字段改为 `input[placeholder*="概括视频主要内容"]`（独立字段，非拼入正文）
- 描述字段改为 `div[contenteditable]`（匹配 `contenteditable=""`）

### Changed (Instagram)
- 创建帖子按钮改为 `[aria-label="新帖子"]`（中文界面），兼容多语言 fallback

### Added
- `vp-accounts remove` 命令：解绑账号组中某平台的登录状态并清除本地 Profile
- 所有发布脚本整体 `try/except Exception: pass` 包裹，防止用户提前关闭浏览器导致报错

---

## [1.0.0] - 2026-02

### Added
- 初始版本：支持抖音、小红书、微信视频号、Threads、Instagram 五平台发布
- `vp-accounts`：账号组管理，支持 `add / delete / list / login / status` 命令
- `vp-publish-douyin`：抖音视频发布，自动填写标题 / 正文 / 标签
- `vp-publish-xhs`：小红书视频 / 图片发布，自动切换发布模式
- `vp-publish-shipinhao`：微信视频号发布，微信扫码登录
- `vp-publish-threads`：Threads 发布，支持纯文字或带媒体
- `vp-publish-ins`：Instagram 发布，自动点击多步骤流程（裁剪 → 滤镜 → Caption）
- `vp-publish`：多平台编排 SKILL.md，一次指令依次发布
- Session 持久化存储至 `profile/` 目录，登录一次长期复用
- 半自动设计：脚本填写内容，用户手动点击发布按钮
