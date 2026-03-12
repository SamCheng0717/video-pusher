# Video Pusher Skills 设计文档

**日期**：2026-03-12
**项目**：video-pusher
**目标**：将医美内容发布工具重构为可发布到 clawhub 的 Claude Code skill 集合

---

## 背景

原项目（`/Users/chengsen/Projects/医美内容发布工具`）是一个基于 Streamlit + Playwright 的多平台视频/图文发布工具，支持抖音、小红书、视频号、Threads、Instagram 五个平台，已稳定运行。

本次目标：将其重构为独立、可发布的 Claude Code skill 包，原项目保持不变。

---

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 执行模式 | 重写为独立 Python 工具 | 需发布到 clawhub，必须自包含，不依赖原项目路径 |
| 平台拆分 | 每个平台一个 skill | 单一职责；用户可单独使用某平台；便于独立调试 |
| 账号组管理 | 合并到 `vp-accounts` | 登录状态管理与账号组是同一关注点 |
| 编排层 | 独立的 `vp-publish` skill | 提供"一键发布到多平台"的统一入口 |
| Profile 路径 | `video-pusher/profile/` | 所有脚本共享同一 profile 目录，避免分散 |
| Git 策略 | `profile/` 加入 `.gitignore` | 包含 Chromium Session/Cookie，不可提交 |
| CLI 接口变化 | `--group <name>` 替代原 `--profile <subpath>` | 新脚本内部查询 accounts.json 完成路径解析，调用方无需关心存储细节 |
| Threads/Instagram 登录 | 新增专用登录命令（原项目仅支持3平台） | 统一登录管理体验，不依赖发布时临时等待 |

---

## 目录结构

```
/Users/chengsen/Projects/video-pusher/
├── .gitignore
├── profile/                          # 运行时生成，gitignore
│   ├── accounts.json                 # 账号组配置
│   ├── douyin/group_0/               # Chromium 持久化 Session
│   ├── xhs/group_0/
│   ├── shipinhao/group_0/
│   ├── threads/group_0/
│   └── ins/group_0/
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-12-video-pusher-skills-design.md
└── skills/
    ├── vp-accounts/
    │   ├── SKILL.md
    │   └── vp_accounts.py
    ├── vp-publish/
    │   └── SKILL.md
    ├── vp-publish-douyin/
    │   ├── SKILL.md
    │   └── publish_douyin.py
    ├── vp-publish-xhs/
    │   ├── SKILL.md
    │   └── publish_xhs.py
    ├── vp-publish-shipinhao/
    │   ├── SKILL.md
    │   └── publish_shipinhao.py
    ├── vp-publish-threads/
    │   ├── SKILL.md
    │   └── publish_threads.py
    └── vp-publish-ins/
        ├── SKILL.md
        └── publish_ins.py
```

---

## Skill 清单（共 7 个）

### 1. `vp-accounts`

**触发条件**：用户查询登录状态、管理账号组、发起某平台登录
**职责**：
- 读写 `profile/accounts.json`（账号组增删改查）
- 检查各平台 profile 目录是否存在（判断是否已登录）
- 调用 Playwright 打开浏览器触发登录，等待用户完成后保存 session

**支持的平台（全部 5 个）**：

| platform | 登录目标 URL |
|----------|-------------|
| `douyin` | https://creator.douyin.com/creator-micro/content/upload |
| `xhs` | https://creator.xiaohongshu.com/publish/publish |
| `shipinhao` | https://channels.weixin.qq.com/platform/post/create |
| `threads` | https://www.threads.net/ |
| `ins` | https://www.instagram.com/ |

> 注：原项目 `login_account.py` 仅支持前三个平台。`vp_accounts.py` 新增 threads/ins 登录支持，使用相同的 Playwright 持久化 context 机制。

**`vp_accounts.py` 命令接口**：
```
python vp_accounts.py list                          # 列出所有账号组及登录状态（JSON 输出）
python vp_accounts.py add <name>                    # 创建账号组
python vp_accounts.py delete <name>                 # 删除账号组
python vp_accounts.py login <name> <platform>       # 触发登录（阻塞至浏览器关闭，完成后自动写入 accounts.json）
python vp_accounts.py status <name> <platform>      # 检查登录状态
```

**`login` 命令完整执行流程**：
1. 从 accounts.json 查找账号组，计算 profile 子路径（`{platform}/group_{index}`）
2. 创建 profile 目录（`os.makedirs(..., exist_ok=True)`）
3. 清理 Singleton 锁文件
4. 用 Playwright 打开持久化浏览器，导航到对应平台登录页
5. 等待用户完成登录并**关闭浏览器窗口**（`context.wait_for_event("close", timeout=0)`）
6. 将 `platforms[platform] = profile_subpath` 写入 accounts.json
7. 打印"✅ {platform} 登录完成，Session 已保存"

> **关键**：步骤 6 的写回 accounts.json 是新设计相对于原项目的核心区别。原项目中这一步由 Streamlit UI 手动触发，新设计在浏览器关闭后自动完成。

**`status` 命令退出码约定**：
- 退出码 `0`：已登录
- 退出码 `1`：未登录

**`status` 判断逻辑**（两步验证）：
1. 检查 `accounts.json` 中该账号组的 `platforms` 字典是否包含该平台 key（主要依据）
2. 检查对应 profile 目录是否存在（辅助验证）

两者都满足才视为已登录，否则返回退出码 `1`。单纯检查目录存在不够可靠。

**`list` 命令输出格式**（JSON，供 Claude 解析）：
```json
[
  {
    "name": "A组",
    "platforms": {
      "douyin": true,
      "xhs": false,
      "shipinhao": true,
      "threads": false,
      "ins": false
    }
  }
]
```

`platforms` 中 `true` 表示该平台 key 存在于 `accounts.json` 对应账号组中（已登录），`false` 表示不存在（未登录）。`list` 始终输出全部 5 个平台，对不存在的 key 补 `false`。

`profile/accounts.json` 不存在时，`list` 返回空数组 `[]`，退出码 `0`。

---

### 2. `vp-publish`

**触发条件**：用户说"发布视频/内容到多平台"、"一键发布"
**职责**：
- 引导用户选择目标平台和账号组
- 调用 `vp_accounts.py status` 验证登录状态
- 未登录处理：询问用户"是否先登录，还是跳过该平台"，等待用户决策后继续
- 按顺序调用各平台 publish skill
- 汇报发布结果

**无 Python 脚本**，纯 Claude 编排逻辑。

---

### 3-7. `vp-publish-{platform}`

适用平台：`douyin` / `xhs` / `shipinhao` / `threads` / `ins`

**触发条件**：用户指定单平台发布
**职责**：
- 接收文件路径、标题、正文、标签、账号组名称
- 用 Bash 运行对应 `publish_<platform>.py`（脚本会阻塞，等用户在浏览器完成发布后按回车）
- 提示用户：浏览器打开后请检查内容并点击发布，完成后在终端按回车关闭

**各发布脚本启动流程（通用）**：
1. 从 accounts.json 查找账号组，拼接 `user_data_dir`
2. 清理 Singleton 锁文件（见 Profile 路径约定章节）
3. 启动 Playwright 持久化浏览器，导航到发布页
4. 检测登录状态，如未登录等待用户完成登录（timeout=120s）
5. 执行平台特定的发布操作（见"各平台发布流程细节"）
6. 打印提示后阻塞：`input("\n发布完成后按回车关闭浏览器...")`
7. `context.close()`

**`publish_<platform>.py` 接口**（统一）：
```
python publish_douyin.py \
  --file <path> \
  --title <title> \
  --description <desc> \
  --tags <tags> \
  --group <group_name>
```

> **`--group` 与原项目的区别**：原项目传 `--profile douyin/group_0`（profile 子路径）。新脚本接受 `--group A组`（账号组名），在脚本内部查询 `accounts.json` 获取对应 profile 子路径，再拼接 `PROFILE_BASE` 得到 `user_data_dir`。调用方无需关心路径细节。

**`--file` 和 `--title` 参数的必填性**：

| platform | `--file` | `--title` | 说明 |
|----------|----------|-----------|------|
| `douyin` | 必填 | 必填 | 视频；标题填入独立 input |
| `xhs` | 必填 | 必填 | 视频或图片；标题填入独立 input |
| `shipinhao` | 必填 | 必填 | 视频；**无独立标题字段**（见下方注意） |
| `threads` | 可选 | 必填 | 支持纯文字；`--file` 为空跳过上传 |
| `ins` | 可选 | 必填 | 支持纯文字；`--file` 为空跳过上传 |

---

## Playwright 启动参数规范

所有脚本（登录和发布）的 `launch_persistent_context` 使用**统一参数**，不得遗漏：

```python
context = p.chromium.launch_persistent_context(
    user_data_dir=profile_dir,
    headless=False,
    args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
    ignore_default_args=["--enable-automation"],
    no_viewport=True,
)
page = context.new_page()
page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
```

> 这些参数的作用：反自动化检测（否则抖音/小红书会拦截）、全屏启动、禁用视口约束。**缺少任何一个参数可能导致平台识别为机器人。**

登录脚本等待浏览器被用户手动关闭：

```python
try:
    context.wait_for_event("close", timeout=0)  # timeout=0 表示无超时，永久阻塞
except Exception:
    pass
```

---

## 各平台发布流程细节

### 标签格式化规则（所有平台统一）

```python
# tags 参数为空格分隔的字符串，如 "医美 玻尿酸 韩国整形"
if tags:
    tag_str = " ".join("#" + t.strip().lstrip("#") for t in tags.split())
    # 结果："#医美 #玻尿酸 #韩国整形"
    # strip() 去除空白，lstrip("#") 避免用户已加 # 导致重复
```

### 登录检测逻辑（所有平台）

`page.goto()` 并 `wait_for_load_state("networkidle")` 后检测：

| platform | 登录检测条件 |
|----------|------------|
| `douyin` | `"login" in page.url` 或 `"passport" in page.url` |
| `xhs` | `"login" in page.url` 或 `"sign" in page.url` |
| `shipinhao` | `"login" in page.url` 或 `page.locator('canvas').count() > 0` |
| `threads` | `"login" in page.url` 或 `page.locator('input[name="username"]').count() > 0` |
| `ins` | `"accounts/login" in page.url` 或 `page.locator('input[name="username"]').count() > 0` |

检测到未登录时打印提示，用 `wait_for_url` 等待（timeout=120000ms），完成后 `time.sleep(2~3)`。

### 文件上传（所有平台统一 selector，平台间等待时间不同）

```python
page.wait_for_selector('input[type="file"]', timeout=30000)
page.locator('input[type="file"]').first.set_input_files(file_path)
```

上传后各平台等待时间（让平台处理文件）：

| platform | 上传后 sleep |
|----------|------------|
| `douyin` | `time.sleep(8)` |
| `xhs` | `time.sleep(8)` |
| `shipinhao` | `time.sleep(10)` |
| `threads` | `time.sleep(4)` |
| `ins` | `time.sleep(4)` |

### 文案组合方式与填写操作

各平台标题/正文处理方式**不同**，必须严格按此实现：

| platform | 标题处理 | 正文 selector | 填写操作 |
|----------|---------|--------------|---------|
| `douyin` | `wait_for_selector('input[placeholder*="标题"], input[placeholder*="请输入"]', timeout=60000)` → `click()` → `fill(title)` | `'div[contenteditable="true"]'` | `click()` → `type(desc+tags, delay=30)` |
| `xhs` | `wait_for_selector('input[placeholder*="标题"], input[placeholder*="填写标题"]', timeout=60000)` → `click()` → `fill(title)` | `'div[contenteditable="true"]'` | `click()` → `sleep(0.5)` → `type(desc+tags, delay=30)` |
| `shipinhao` | **无独立标题字段** | `'textarea, div[contenteditable="true"]'` | `click()` → `sleep(0.5)` → **`fill("")`清空** → `type(title+"\n"+desc+tags, delay=30)` |
| `threads` | **无标题字段** | `'div[contenteditable="true"], textarea[placeholder]'` | `click()` → `type(title+"\n"+desc+tags, delay=30)` |
| `ins` | **无标题字段** | `'textarea[aria-label*="caption"], textarea[placeholder*="caption"], div[aria-label*="caption"], textarea[placeholder*="Write"]'` | `click()` → `sleep(0.5)` → `type(title+"\n"+desc+tags, delay=30)` |

> ⚠️ **视频号必须先 `fill("")` 清空**，否则页面残留内容会混入发布文案。
>
> ⚠️ **`type()` 而非 `fill()`** 用于正文区，`type()` 模拟键盘输入（delay=30ms/字），平台编辑器能正确响应；`fill()` 直接设值，contenteditable 区域可能无效。标题 input 用 `fill()` 因为是普通 input 元素。

### 小红书：视频/图文模式切换

```python
ext = os.path.splitext(file_path)[1].lower()
if ext in [".mp4", ".mov", ".avi", ".mkv"]:
    try:
        btn = page.locator('text=发布视频').first
        if btn.is_visible():
            btn.click()
            time.sleep(1)   # 等待页面切换到视频模式
    except Exception:
        pass
# 切换完成后再执行 wait_for_selector('input[type="file"]')
```

### Threads：发帖按钮

```python
compose_sel = '[aria-label="New thread"], [aria-label="发帖"], a[href="/new-post"]'
page.wait_for_selector(compose_sel, timeout=15000)
page.locator(compose_sel).first.click()
time.sleep(1)
```

### Instagram：多步骤发布流程

Caption 在最后一步才出现，上传后需循环点击"下一步"：

```python
# 上传文件后执行（只在有文件时）：
for step_label in ["Next", "下一步", "OK"]:
    try:
        btn = page.locator(
            f'button:has-text("{step_label}"), [aria-label="{step_label}"]'
        ).first
        if btn.is_visible():
            btn.click()
            time.sleep(2)
    except Exception:
        pass
# 之后再填写 Caption
```

### 异常处理策略（所有脚本统一）

所有 UI 操作用 `try/except` 包装，失败时**打印提示而不中止**，让用户手动完成：

```python
try:
    # UI 操作（填写标题、正文、上传等）
    ...
except Exception:
    print("⚠️  <操作名称>请手动完成")
```

唯一例外：文件上传失败时某些平台（抖音）改为 `input("登录后按回车继续...")` 等待用户介入。

### 发布确认机制

所有发布脚本的最后一步：

```python
print("\n✅ 内容填写完毕！请检查后点击【发布】按钮")
input("\n发布完成后按回车关闭浏览器...")
context.close()
```

脚本**阻塞**等待用户按回车。Claude 调用脚本后须告知用户："浏览器已打开，请检查内容并点击发布，完成后回到终端按回车。"

---

## 数据流

### 正常发布（均已登录）

```
用户: "发布这个视频到抖音和小红书，使用A组账号"
        ↓
  vp-publish
    1. 解析平台列表 [douyin, xhs]，账号组 [A组]
    2. python vp_accounts.py status A组 douyin → exit 0（已登录）
    3. python vp_accounts.py status A组 xhs → exit 0（已登录）
    4. 调用 vp-publish-douyin（传入文件、内容、A组）
    5. 调用 vp-publish-xhs（传入文件、内容、A组）
    6. 汇报结果
```

### 未登录分支

```
  vp-publish
    2. python vp_accounts.py status A组 xhs → exit 1（未登录）
       → 询问用户：
         [a] 先登录小红书再继续
         [b] 跳过小红书，只发抖音
    用户选 [a] → 调用 vp-accounts 完成登录 → 继续发布
    用户选 [b] → 跳过 xhs，继续其他平台
```

---

## Profile 路径约定

### PROFILE_BASE 计算方式

所有脚本都在 `skills/<skill-name>/` 下，需要向上**三级**才能到 `video-pusher/`：

```
video-pusher/skills/vp-publish-douyin/publish_douyin.py
              ↑3        ↑2                ↑1
```

```python
# 所有 Python 脚本（publish_*.py 和 vp_accounts.py）统一使用：
PROFILE_BASE = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    ),
    "profile"
)
# 解析为：video-pusher/profile/
```

> ⚠️ 错误写法（两层 dirname）会解析到 `video-pusher/skills/profile/`，是错误路径。

### profile 子路径生成规则

子路径格式为 `{platform}/group_{index}`，其中 `index` 是该账号组在 `accounts.json` 数组中的下标（0-based）：

```python
index = next(i for i, g in enumerate(accounts) if g["name"] == group_name)
profile_subpath = f"{platform}/group_{index}"   # e.g. "douyin/group_0"
user_data_dir = os.path.join(PROFILE_BASE, profile_subpath)
```

示例：
- "A组" 在数组下标 0，抖音 profile → `video-pusher/profile/douyin/group_0/`
- "B组" 在数组下标 1，抖音 profile → `video-pusher/profile/douyin/group_1/`

**`accounts.json` 中的路径为相对于 `PROFILE_BASE` 的子路径**：

```python
# user_data_dir 的计算方式（供 --group 参数使用）
group = next(g for g in accounts if g["name"] == group_name)
profile_subpath = group["platforms"][platform]          # e.g. "douyin/group_0"
user_data_dir = os.path.join(PROFILE_BASE, profile_subpath)  # video-pusher/profile/douyin/group_0/
```

### Singleton 锁文件清理

每次启动浏览器前（**登录和发布脚本都需要**），必须清理 Chromium 遗留的锁文件，否则上次异常退出会导致 "profile already in use" 错误：

```python
for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    lp = os.path.join(profile_dir, lock)
    if os.path.exists(lp):
        os.remove(lp)
```

**`accounts.json` 完整结构**（支持多账号组）：

```json
[
  {
    "name": "A组",
    "platforms": {
      "douyin": "douyin/group_0",
      "xhs": "xhs/group_0"
    }
  },
  {
    "name": "B组",
    "platforms": {
      "douyin": "douyin/group_1"
    }
  }
]
```

`platforms` 中只记录已登录的平台，未登录的平台不出现在字典中。

---

## SKILL.md 模板

每个 skill 的 `SKILL.md` 最小结构：

```markdown
---
name: vp-accounts
description: Use when managing video publisher account groups, checking login status, or initiating platform login for douyin/xhs/shipinhao/threads/instagram
---

# vp-accounts

## Overview
...
```

frontmatter 仅 `name` 和 `description` 两个字段（clawhub 要求），`description` 用英文，以 "Use when..." 开头。

---

## .gitignore

```
profile/
__pycache__/
*.pyc
.DS_Store
```

---

## 依赖

- **Python**：>= 3.8
- **playwright**：>= 1.40

安装：
```bash
pip install playwright
playwright install chromium
```

---

## clawhub 发布要求

- 每个 skill 目录包含 `SKILL.md`（frontmatter 含 `name` 和 `description`）
- `profile/` 不打包（.gitignore）
- Python 脚本作为 skill 的 supporting files 一同发布
