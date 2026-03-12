# Video Pusher Skills Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将医美内容发布工具重构为 7 个独立的 Claude Code skill，支持抖音、小红书、视频号、Threads、Instagram 五平台发布，可发布到 clawhub。

**Architecture:** 每个 skill 包含 SKILL.md 指南和对应 Python 脚本。`vp_accounts.py` 管理账号组和登录状态，`publish_*.py` 各自负责单平台 Playwright 自动化发布，`vp-publish` 是纯编排 skill。所有脚本共享 `video-pusher/profile/` 目录存储 Chromium session。

**Tech Stack:** Python >= 3.8, playwright >= 1.40, chromium

**Spec:** `docs/superpowers/specs/2026-03-12-video-pusher-skills-design.md`

---

## Chunk 1: 基础设施 + vp_accounts.py

### Task 1: 项目脚手架

**Files:**
- Create: `.gitignore`
- Create: `skills/vp-accounts/` (目录)
- Create: `skills/vp-publish/` (目录)
- Create: `skills/vp-publish-douyin/` (目录)
- Create: `skills/vp-publish-xhs/` (目录)
- Create: `skills/vp-publish-shipinhao/` (目录)
- Create: `skills/vp-publish-threads/` (目录)
- Create: `skills/vp-publish-ins/` (目录)
- Create: `tests/` (目录)

- [ ] **Step 1: 创建 .gitignore**

```
profile/
__pycache__/
*.pyc
.DS_Store
*.egg-info/
.pytest_cache/
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p skills/vp-accounts skills/vp-publish \
  skills/vp-publish-douyin skills/vp-publish-xhs \
  skills/vp-publish-shipinhao skills/vp-publish-threads \
  skills/vp-publish-ins tests
```

- [ ] **Step 3: 验证目录结构**

```bash
find skills -type d | sort
```

Expected:
```
skills/vp-accounts
skills/vp-publish
skills/vp-publish-douyin
skills/vp-publish-ins
skills/vp-publish-shipinhao
skills/vp-publish-threads
skills/vp-publish-xhs
```

- [ ] **Step 4: Commit**

```bash
git init
git add .gitignore
git commit -m "chore: init project with .gitignore"
```

---

### Task 2: vp_accounts.py — 纯逻辑层（无 Playwright）

**Files:**
- Create: `skills/vp-accounts/vp_accounts.py`
- Create: `tests/test_vp_accounts.py`

该任务实现所有**不依赖 Playwright** 的逻辑：accounts.json 读写、profile 路径计算、标签格式化。Playwright 登录部分在 Task 3 实现。

- [ ] **Step 1: 写失败测试 — PROFILE_BASE 路径计算**

```python
# tests/test_vp_accounts.py
import os, sys, json, tempfile, pytest

# 让测试能 import vp_accounts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-accounts'))
import vp_accounts

def test_profile_base_is_three_levels_up():
    """PROFILE_BASE 必须指向 video-pusher/profile/，即脚本上三级"""
    base = vp_accounts.PROFILE_BASE
    # 脚本在 skills/vp-accounts/vp_accounts.py
    # 三级向上应到达 video-pusher/
    assert base.endswith('profile')
    assert 'skills' not in base  # 不能落在 skills/ 内
```

- [ ] **Step 2: 运行，确认失败**

```bash
cd /Users/chengsen/Projects/video-pusher
python -m pytest tests/test_vp_accounts.py::test_profile_base_is_three_levels_up -v
```

Expected: `ImportError` 或 `AttributeError`（模块不存在）

- [ ] **Step 3: 写失败测试 — accounts.json 基本操作**

在 `tests/test_vp_accounts.py` 追加：

```python
def test_load_accounts_returns_empty_when_file_missing(tmp_path):
    accounts = vp_accounts.load_accounts(tmp_path / 'accounts.json')
    assert accounts == []

def test_save_and_load_accounts(tmp_path):
    path = tmp_path / 'accounts.json'
    data = [{'name': 'A组', 'platforms': {'douyin': 'douyin/group_0'}}]
    vp_accounts.save_accounts(path, data)
    loaded = vp_accounts.load_accounts(path)
    assert loaded == data

def test_get_profile_subpath():
    accounts = [
        {'name': 'A组', 'platforms': {}},
        {'name': 'B组', 'platforms': {}},
    ]
    assert vp_accounts.get_profile_subpath(accounts, 'A组', 'douyin') == 'douyin/group_0'
    assert vp_accounts.get_profile_subpath(accounts, 'B组', 'douyin') == 'douyin/group_1'

def test_get_profile_subpath_raises_when_group_not_found():
    with pytest.raises(ValueError, match='不存在'):
        vp_accounts.get_profile_subpath([], '不存在组', 'douyin')

def test_format_tags():
    assert vp_accounts.format_tags('医美 玻尿酸') == '#医美 #玻尿酸'
    assert vp_accounts.format_tags('#医美 #玻尿酸') == '#医美 #玻尿酸'   # 已有 # 不重复
    assert vp_accounts.format_tags('') == ''
    assert vp_accounts.format_tags(None) == ''
```

- [ ] **Step 4: 运行，确认所有测试失败**

```bash
python -m pytest tests/test_vp_accounts.py -v
```

Expected: 全部 `FAILED`（模块不存在）

- [ ] **Step 5: 实现 vp_accounts.py 纯逻辑部分**

```python
# skills/vp-accounts/vp_accounts.py
import os, sys, json, argparse
from pathlib import Path

# ── 路径常量 ────────────────────────────────────────────────
# 脚本位于 skills/vp-accounts/vp_accounts.py
# 向上三级到达 video-pusher/
PROFILE_BASE = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    ),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")

PLATFORM_URLS = {
    "douyin":    "https://creator.douyin.com/creator-micro/content/upload",
    "xhs":       "https://creator.xiaohongshu.com/publish/publish",
    "shipinhao": "https://channels.weixin.qq.com/platform/post/create",
    "threads":   "https://www.threads.net/",
    "ins":       "https://www.instagram.com/",
}
PLATFORMS = list(PLATFORM_URLS.keys())

# ── 纯逻辑函数 ──────────────────────────────────────────────

def load_accounts(path=None):
    """读取 accounts.json，文件不存在时返回空列表"""
    p = Path(path or ACCOUNTS_FILE)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_accounts(path_or_list, data=None):
    """保存 accounts.json
    用法：save_accounts(accounts)  或  save_accounts(path, accounts)
    """
    if data is None:
        path, data = ACCOUNTS_FILE, path_or_list
    else:
        path = path_or_list
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_profile_subpath(accounts, group_name, platform):
    """返回 '{platform}/group_{index}'，账号组不存在时 raise ValueError"""
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            return f"{platform}/group_{i}"
    raise ValueError(f"账号组「{group_name}」不存在")

def format_tags(tags):
    """将空格分隔的标签规范化为 '#tag1 #tag2' 格式"""
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())

def clear_singleton_locks(profile_dir):
    """清理 Chromium 遗留的锁文件，防止 'profile already in use' 错误"""
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)
```

- [ ] **Step 6: 运行测试，确认通过**

```bash
python -m pytest tests/test_vp_accounts.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 7: Commit**

```bash
git add skills/vp-accounts/vp_accounts.py tests/test_vp_accounts.py
git commit -m "feat: add vp_accounts core logic (accounts.json, path calc, tag format)"
```

---

### Task 3: vp_accounts.py — CLI 命令（list / add / delete / status）

**Files:**
- Modify: `skills/vp-accounts/vp_accounts.py`
- Modify: `tests/test_vp_accounts.py`

- [ ] **Step 1: 写失败测试 — CLI 命令**

追加到 `tests/test_vp_accounts.py`：

```python
import subprocess

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-accounts', 'vp_accounts.py')

def run(args, env_overrides=None):
    """运行 vp_accounts.py 并返回 (returncode, stdout)"""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    r = subprocess.run([sys.executable, SCRIPT] + args,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip()

def test_cli_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    code, out = run(['list'])
    assert code == 0
    assert json.loads(out) == []

def test_cli_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    run(['add', 'A组'])
    code, out = run(['list'])
    assert code == 0
    data = json.loads(out)
    assert data[0]['name'] == 'A组'
    assert data[0]['platforms']['douyin'] == False

def test_cli_add_duplicate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    run(['add', 'A组'])
    code, _ = run(['add', 'A组'])
    assert code == 1

def test_cli_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    run(['add', 'A组'])
    run(['delete', 'A组'])
    code, out = run(['list'])
    assert json.loads(out) == []

def test_cli_status_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    run(['add', 'A组'])
    code, _ = run(['status', 'A组', 'douyin'])
    assert code == 1   # 未登录

def test_cli_status_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    # 手动写入已登录记录
    data = [{'name': 'A组', 'platforms': {'douyin': 'douyin/group_0'}}]
    vp_accounts.save_accounts(str(tmp_path / 'accounts.json'), data)
    # 创建 profile 目录（status 需要目录也存在）
    os.makedirs(os.path.join(vp_accounts.PROFILE_BASE, 'douyin', 'group_0'), exist_ok=True)
    code, _ = run(['status', 'A组', 'douyin'])
    assert code == 0   # 已登录
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_vp_accounts.py -k "cli" -v
```

Expected: 全部 `FAILED`

- [ ] **Step 3: 实现 CLI 命令（追加到 vp_accounts.py）**

在 `vp_accounts.py` 末尾追加：

```python
# ── CLI 命令实现 ────────────────────────────────────────────

def cmd_list():
    accounts = load_accounts()
    output = []
    for g in accounts:
        platforms_status = {p: p in g.get("platforms", {}) for p in PLATFORMS}
        output.append({"name": g["name"], "platforms": platforms_status})
    print(json.dumps(output, ensure_ascii=False, indent=2))

def cmd_add(name):
    accounts = load_accounts()
    if any(g["name"] == name for g in accounts):
        print(f"错误：账号组「{name}」已存在", file=sys.stderr)
        sys.exit(1)
    accounts.append({"name": name, "platforms": {}})
    save_accounts(accounts)
    print(f"✅ 账号组「{name}」已创建")

def cmd_delete(name):
    accounts = load_accounts()
    new = [g for g in accounts if g["name"] != name]
    if len(new) == len(accounts):
        print(f"错误：账号组「{name}」不存在", file=sys.stderr)
        sys.exit(1)
    save_accounts(new)
    print(f"✅ 账号组「{name}」已删除")

def cmd_status(group_name, platform):
    if platform not in PLATFORMS:
        print(f"错误：不支持的平台 {platform}，可选：{PLATFORMS}", file=sys.stderr)
        sys.exit(1)
    accounts = load_accounts()
    group = next((g for g in accounts if g["name"] == group_name), None)
    if group is None:
        print(f"错误：账号组「{group_name}」不存在", file=sys.stderr)
        sys.exit(1)
    # 两步验证：1. accounts.json 中有此平台 key；2. profile 目录存在
    subpath = group.get("platforms", {}).get(platform)
    if not subpath:
        sys.exit(1)
    profile_dir = os.path.join(PROFILE_BASE, subpath)
    if not os.path.isdir(profile_dir):
        sys.exit(1)
    sys.exit(0)

# ── 入口 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="vp_accounts")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    p_add = sub.add_parser("add")
    p_add.add_argument("name")

    p_del = sub.add_parser("delete")
    p_del.add_argument("name")

    p_login = sub.add_parser("login")
    p_login.add_argument("name")
    p_login.add_argument("platform", choices=PLATFORMS)

    p_status = sub.add_parser("status")
    p_status.add_argument("name")
    p_status.add_argument("platform", choices=PLATFORMS)

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "add":
        cmd_add(args.name)
    elif args.cmd == "delete":
        cmd_delete(args.name)
    elif args.cmd == "login":
        cmd_login(args.name, args.platform)
    elif args.cmd == "status":
        cmd_status(args.name, args.platform)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python -m pytest tests/test_vp_accounts.py -v
```

Expected: 全部 `PASSED`（注意：`test_cli_status_logged_in` 因 profile 目录创建逻辑可能需要调整 monkeypatch，确保 PROFILE_BASE 也被覆盖）

- [ ] **Step 5: Commit**

```bash
git add skills/vp-accounts/vp_accounts.py tests/test_vp_accounts.py
git commit -m "feat: add vp_accounts CLI commands (list/add/delete/status)"
```

---

### Task 4: vp_accounts.py — login 命令（Playwright）

**Files:**
- Modify: `skills/vp-accounts/vp_accounts.py`

login 命令依赖真实浏览器，无法单元测试。用手动集成测试验证。

- [ ] **Step 1: 在 vp_accounts.py 中实现 cmd_login（追加在 cmd_status 之前）**

```python
def cmd_login(group_name, platform):
    from playwright.sync_api import sync_playwright

    accounts = load_accounts()
    group = next((g for g in accounts if g["name"] == group_name), None)
    if group is None:
        print(f"错误：账号组「{group_name}」不存在，请先用 add 命令创建", file=sys.stderr)
        sys.exit(1)

    subpath = get_profile_subpath(accounts, group_name, platform)
    profile_dir = os.path.join(PROFILE_BASE, subpath)
    os.makedirs(profile_dir, exist_ok=True)
    clear_singleton_locks(profile_dir)

    url = PLATFORM_URLS[platform]
    platform_names = {
        "douyin": "抖音", "xhs": "小红书", "shipinhao": "视频号",
        "threads": "Threads", "ins": "Instagram",
    }
    print(f"\n正在打开 {platform_names[platform]} 登录页面…")
    print("请在浏览器中完成登录，登录成功后关闭浏览器窗口。\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto(url)
        try:
            context.wait_for_event("close", timeout=0)  # 无超时，等用户关闭浏览器
        except Exception:
            pass

    # 浏览器已关闭，写回 accounts.json
    group.setdefault("platforms", {})[platform] = subpath
    save_accounts(accounts)
    print(f"✅ {platform_names[platform]} 登录完成，Session 已保存至 {profile_dir}")
```

- [ ] **Step 2: 验证 argparse 可解析所有命令**

```bash
python skills/vp-accounts/vp_accounts.py --help
python skills/vp-accounts/vp_accounts.py list
python skills/vp-accounts/vp_accounts.py add "测试组"
python skills/vp-accounts/vp_accounts.py list
python skills/vp-accounts/vp_accounts.py status "测试组" douyin ; echo "exit: $?"
python skills/vp-accounts/vp_accounts.py delete "测试组"
```

Expected:
```
[]
✅ 账号组「测试组」已创建
[{"name": "测试组", "platforms": {...all false...}}]
exit: 1
✅ 账号组「测试组」已删除
```

- [ ] **Step 3: 手动集成测试 login（需要真实网络）**

```bash
python skills/vp-accounts/vp_accounts.py add "集成测试组"
python skills/vp-accounts/vp_accounts.py login "集成测试组" douyin
# 浏览器打开后完成登录，关闭浏览器
python skills/vp-accounts/vp_accounts.py status "集成测试组" douyin ; echo "exit: $?"
# Expected: exit: 0
python skills/vp-accounts/vp_accounts.py delete "集成测试组"
```

- [ ] **Step 4: Commit**

```bash
git add skills/vp-accounts/vp_accounts.py
git commit -m "feat: add vp_accounts login command with Playwright"
```

---

### Task 5: vp-accounts SKILL.md

**Files:**
- Create: `skills/vp-accounts/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
pip install playwright
playwright install chromium
```
```

- [ ] **Step 2: 验证 frontmatter 格式**

```bash
head -6 skills/vp-accounts/SKILL.md
```

Expected: 包含 `name:` 和 `description:` 两行，且 `description` 以 "Use when" 开头。

- [ ] **Step 3: Commit**

```bash
git add skills/vp-accounts/SKILL.md
git commit -m "feat: add vp-accounts SKILL.md"
```

---

## Chunk 2: 发布脚本（抖音 / 小红书 / 视频号）

### Task 6: publish_douyin.py

**Files:**
- Create: `skills/vp-publish-douyin/publish_douyin.py`
- Modify: `tests/test_vp_accounts.py`（复用 format_tags 测试已覆盖）

- [ ] **Step 1: 写失败测试 — 参数解析与路径计算**

创建 `tests/test_publish_douyin.py`：

```python
import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-douyin'))

def test_script_requires_file():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-douyin/publish_douyin.py',
         '--title', 'test', '--description', 'x', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --file 是必填项

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-douyin/publish_douyin.py',
         '--file', '/tmp/x.mp4', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --title 是必填项

def test_profile_base_three_levels_up():
    import publish_douyin
    assert 'skills' not in publish_douyin.PROFILE_BASE
    assert publish_douyin.PROFILE_BASE.endswith('profile')
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_publish_douyin.py -v
```

Expected: `ImportError` 或 `ModuleNotFoundError`

- [ ] **Step 3: 实现 publish_douyin.py**

```python
# skills/vp-publish-douyin/publish_douyin.py
"""抖音自动发布脚本"""
import argparse, time, os, sys, json

PROFILE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")


def load_profile_dir(group_name):
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError(f"accounts.json 不存在，请先用 vp_accounts.py add 创建账号组")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        accounts = json.load(f)
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            subpath = g.get("platforms", {}).get("douyin")
            if not subpath:
                raise ValueError(f"账号组「{group_name}」未登录抖音，请先执行 vp_accounts.py login")
            return os.path.join(PROFILE_BASE, subpath)
    raise ValueError(f"账号组「{group_name}」不存在")


def clear_locks(profile_dir):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)


def format_tags(tags):
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())


def publish(file_path, title, description, tags, group):
    from playwright.sync_api import sync_playwright

    profile_dir = load_profile_dir(group)
    os.makedirs(profile_dir, exist_ok=True)
    clear_locks(profile_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto("https://creator.douyin.com/creator-micro/content/upload")
        page.wait_for_load_state("networkidle")

        if "login" in page.url or "passport" in page.url:
            print("⚠️  请在浏览器中完成登录...")
            page.wait_for_url("**/creator-micro/**", timeout=120000)
            time.sleep(2)

        try:
            page.wait_for_selector('input[type="file"]', timeout=30000)
        except Exception:
            input("登录后按回车继续...")
            page.wait_for_selector('input[type="file"]', timeout=30000)

        print(f"📤 正在上传：{os.path.basename(file_path)}")
        page.locator('input[type="file"]').first.set_input_files(file_path)
        time.sleep(8)

        try:
            title_sel = 'input[placeholder*="标题"], input[placeholder*="请输入"]'
            page.wait_for_selector(title_sel, timeout=60000)
            ti = page.locator(title_sel).first
            ti.click()
            ti.fill(title)
        except Exception:
            print("⚠️  标题请手动填写")

        try:
            desc_area = page.locator('div[contenteditable="true"]').first
            desc_area.click()
            full_text = description or ""
            tag_str = format_tags(tags)
            if tag_str:
                full_text += "\n" + tag_str
            desc_area.type(full_text, delay=30)
        except Exception:
            print("⚠️  正文请手动填写")

        print("\n✅ 内容填写完毕！请检查后点击【发布】按钮")
        input("\n发布完成后按回车关闭浏览器...")
        context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抖音自动发布")
    parser.add_argument("--file",        required=True,  help="视频文件路径")
    parser.add_argument("--title",       required=True,  help="标题")
    parser.add_argument("--description", default="",     help="正文")
    parser.add_argument("--tags",        default="",     help="标签，空格分隔")
    parser.add_argument("--group",       required=True,  help="账号组名称")
    args = parser.parse_args()
    publish(args.file, args.title, args.description, args.tags, args.group)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_publish_douyin.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/vp-publish-douyin/publish_douyin.py tests/test_publish_douyin.py
git commit -m "feat: add publish_douyin.py"
```

---

### Task 7: vp-publish-douyin SKILL.md

**Files:**
- Create: `skills/vp-publish-douyin/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish-douyin/SKILL.md
git commit -m "feat: add vp-publish-douyin SKILL.md"
```

---

### Task 8: publish_xhs.py

**Files:**
- Create: `skills/vp-publish-xhs/publish_xhs.py`
- Create: `tests/test_publish_xhs.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_publish_xhs.py
import os, sys, subprocess

def test_script_requires_file():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-xhs/publish_xhs.py',
         '--title', 'test', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-xhs'))
    import publish_xhs
    assert 'skills' not in publish_xhs.PROFILE_BASE
    assert publish_xhs.PROFILE_BASE.endswith('profile')
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_publish_xhs.py -v
```

- [ ] **Step 3: 实现 publish_xhs.py**

```python
# skills/vp-publish-xhs/publish_xhs.py
"""小红书自动发布脚本"""
import argparse, time, os, json

PROFILE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")


def load_profile_dir(group_name):
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError("accounts.json 不存在，请先创建账号组")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        accounts = json.load(f)
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            subpath = g.get("platforms", {}).get("xhs")
            if not subpath:
                raise ValueError(f"账号组「{group_name}」未登录小红书")
            return os.path.join(PROFILE_BASE, subpath)
    raise ValueError(f"账号组「{group_name}」不存在")


def clear_locks(profile_dir):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)


def format_tags(tags):
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())


def publish(file_path, title, description, tags, group):
    from playwright.sync_api import sync_playwright

    profile_dir = load_profile_dir(group)
    os.makedirs(profile_dir, exist_ok=True)
    clear_locks(profile_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto("https://creator.xiaohongshu.com/publish/publish")
        page.wait_for_load_state("networkidle")

        if "login" in page.url or "sign" in page.url:
            print("⚠️  请在浏览器中扫码登录小红书...")
            page.wait_for_url("**/publish/**", timeout=120000)
            time.sleep(2)

        # 视频模式切换
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".mp4", ".mov", ".avi", ".mkv"]:
            try:
                btn = page.locator('text=发布视频').first
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)
            except Exception:
                pass

        try:
            page.wait_for_selector('input[type="file"]', timeout=30000)
        except Exception:
            input("登录后按回车继续...")

        print(f"📤 正在上传：{os.path.basename(file_path)}")
        page.locator('input[type="file"]').first.set_input_files(file_path)
        time.sleep(8)

        try:
            title_sel = 'input[placeholder*="标题"], input[placeholder*="填写标题"]'
            page.wait_for_selector(title_sel, timeout=60000)
            ti = page.locator(title_sel).first
            ti.click()
            ti.fill(title)
        except Exception:
            print("⚠️  标题请手动填写")

        try:
            desc_area = page.locator('div[contenteditable="true"]').first
            desc_area.click()
            time.sleep(0.5)
            full_text = description or ""
            tag_str = format_tags(tags)
            if tag_str:
                full_text += "\n" + tag_str
            desc_area.type(full_text, delay=30)
        except Exception:
            print("⚠️  正文请手动填写")

        print("\n✅ 内容填写完毕！请检查后点击【发布】按钮")
        input("\n发布完成后按回车关闭浏览器...")
        context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书自动发布")
    parser.add_argument("--file",        required=True)
    parser.add_argument("--title",       required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags",        default="")
    parser.add_argument("--group",       required=True)
    args = parser.parse_args()
    publish(args.file, args.title, args.description, args.tags, args.group)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_publish_xhs.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/vp-publish-xhs/publish_xhs.py tests/test_publish_xhs.py
git commit -m "feat: add publish_xhs.py"
```

---

### Task 9: vp-publish-xhs SKILL.md

**Files:**
- Create: `skills/vp-publish-xhs/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish-xhs/SKILL.md
git commit -m "feat: add vp-publish-xhs SKILL.md"
```

---

### Task 10: publish_shipinhao.py

**Files:**
- Create: `skills/vp-publish-shipinhao/publish_shipinhao.py`
- Create: `tests/test_publish_shipinhao.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_publish_shipinhao.py
import os, sys, subprocess

def test_script_requires_file():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-shipinhao/publish_shipinhao.py',
         '--title', 'test', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-shipinhao'))
    import publish_shipinhao
    assert 'skills' not in publish_shipinhao.PROFILE_BASE
    assert publish_shipinhao.PROFILE_BASE.endswith('profile')
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_publish_shipinhao.py -v
```

- [ ] **Step 3: 实现 publish_shipinhao.py**

```python
# skills/vp-publish-shipinhao/publish_shipinhao.py
"""视频号自动发布脚本"""
import argparse, time, os, json

PROFILE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")


def load_profile_dir(group_name):
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError("accounts.json 不存在")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        accounts = json.load(f)
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            subpath = g.get("platforms", {}).get("shipinhao")
            if not subpath:
                raise ValueError(f"账号组「{group_name}」未登录视频号")
            return os.path.join(PROFILE_BASE, subpath)
    raise ValueError(f"账号组「{group_name}」不存在")


def clear_locks(profile_dir):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)


def format_tags(tags):
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())


def publish(file_path, title, description, tags, group):
    from playwright.sync_api import sync_playwright

    profile_dir = load_profile_dir(group)
    os.makedirs(profile_dir, exist_ok=True)
    clear_locks(profile_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto("https://channels.weixin.qq.com/platform/post/create")
        page.wait_for_load_state("networkidle")

        if "login" in page.url or page.locator('canvas').count() > 0:
            print("⚠️  请用微信扫描浏览器中的二维码登录...")
            page.wait_for_url("**/platform/**", timeout=120000)
            time.sleep(2)

        try:
            page.wait_for_selector('input[type="file"]', timeout=30000)
            print(f"📤 正在上传：{os.path.basename(file_path)}")
            page.locator('input[type="file"]').first.set_input_files(file_path)
        except Exception:
            print("⚠️  请手动点击上传按钮选择文件")

        time.sleep(10)

        try:
            desc_sel = 'textarea, div[contenteditable="true"]'
            desc_area = page.locator(desc_sel).first
            desc_area.click()
            time.sleep(0.5)
            # 视频号无独立标题字段：标题拼入正文开头
            full_text = title
            if description:
                full_text += "\n" + description
            tag_str = format_tags(tags)
            if tag_str:
                full_text += "\n" + tag_str
            desc_area.fill("")          # 先清空，防止残留内容
            desc_area.type(full_text, delay=30)
        except Exception:
            print("⚠️  内容请手动填写")

        print("\n✅ 内容填写完毕！请检查后点击【发表】按钮")
        input("\n发布完成后按回车关闭浏览器...")
        context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频号自动发布")
    parser.add_argument("--file",        required=True)
    parser.add_argument("--title",       required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags",        default="")
    parser.add_argument("--group",       required=True)
    args = parser.parse_args()
    publish(args.file, args.title, args.description, args.tags, args.group)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_publish_shipinhao.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/vp-publish-shipinhao/publish_shipinhao.py tests/test_publish_shipinhao.py
git commit -m "feat: add publish_shipinhao.py"
```

---

### Task 11: vp-publish-shipinhao SKILL.md

**Files:**
- Create: `skills/vp-publish-shipinhao/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish-shipinhao/SKILL.md
git commit -m "feat: add vp-publish-shipinhao SKILL.md"
```

---

## Chunk 3: 发布脚本（Threads / Instagram）+ 编排 skill

### Task 12: publish_threads.py

**Files:**
- Create: `skills/vp-publish-threads/publish_threads.py`
- Create: `tests/test_publish_threads.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_publish_threads.py
import os, sys, subprocess

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-threads/publish_threads.py',
         '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --title 必填

def test_file_is_optional():
    """threads 不传 --file 不报错（argparse 层面）"""
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-threads/publish_threads.py',
         '--title', 'test', '--group', 'A组', '--help'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode == 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-threads'))
    import publish_threads
    assert 'skills' not in publish_threads.PROFILE_BASE
    assert publish_threads.PROFILE_BASE.endswith('profile')
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_publish_threads.py -v
```

- [ ] **Step 3: 实现 publish_threads.py**

```python
# skills/vp-publish-threads/publish_threads.py
"""Threads 自动发布脚本"""
import argparse, time, os, json

PROFILE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")


def load_profile_dir(group_name):
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError("accounts.json 不存在")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        accounts = json.load(f)
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            subpath = g.get("platforms", {}).get("threads")
            if not subpath:
                raise ValueError(f"账号组「{group_name}」未登录 Threads")
            return os.path.join(PROFILE_BASE, subpath)
    raise ValueError(f"账号组「{group_name}」不存在")


def clear_locks(profile_dir):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)


def format_tags(tags):
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())


def publish(file_path, title, description, tags, group):
    from playwright.sync_api import sync_playwright

    profile_dir = load_profile_dir(group)
    os.makedirs(profile_dir, exist_ok=True)
    clear_locks(profile_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto("https://www.threads.net/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if "login" in page.url or page.locator('input[name="username"]').count() > 0:
            print("⚠️  请在浏览器中完成 Threads 登录...")
            page.wait_for_url("https://www.threads.net/", timeout=120000)
            time.sleep(3)

        # 点击发帖按钮
        try:
            compose_sel = '[aria-label="New thread"], [aria-label="发帖"], a[href="/new-post"]'
            page.wait_for_selector(compose_sel, timeout=15000)
            page.locator(compose_sel).first.click()
            time.sleep(1)
        except Exception:
            print("⚠️  请手动点击发帖按钮")

        # 上传媒体（可选，先上传再填文案）
        if file_path:
            try:
                page.wait_for_selector('input[type="file"]', timeout=15000)
                page.locator('input[type="file"]').first.set_input_files(file_path)
                print(f"📤 文件已上传：{os.path.basename(file_path)}")
                time.sleep(4)
            except Exception:
                print("⚠️  请手动上传文件")

        # 填写文案（title 作正文开头）
        try:
            text_sel = 'div[contenteditable="true"], textarea[placeholder]'
            page.wait_for_selector(text_sel, timeout=15000)
            text_area = page.locator(text_sel).first
            text_area.click()
            full_text = title
            if description:
                full_text += "\n" + description
            tag_str = format_tags(tags)
            if tag_str:
                full_text += "\n" + tag_str
            text_area.type(full_text, delay=30)
            print("✏️  文案已填写")
        except Exception:
            print("⚠️  文案请手动填写")

        print("\n✅ 内容填写完毕！请检查后点击【发帖】按钮")
        input("\n发布完成后按回车关闭浏览器...")
        context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Threads 自动发布")
    parser.add_argument("--file",        default="",    help="媒体文件路径（可选）")
    parser.add_argument("--title",       required=True, help="文案主体（必填）")
    parser.add_argument("--description", default="")
    parser.add_argument("--tags",        default="")
    parser.add_argument("--group",       required=True)
    args = parser.parse_args()
    publish(args.file or None, args.title, args.description, args.tags, args.group)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_publish_threads.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/vp-publish-threads/publish_threads.py tests/test_publish_threads.py
git commit -m "feat: add publish_threads.py"
```

---

### Task 13: vp-publish-threads SKILL.md

**Files:**
- Create: `skills/vp-publish-threads/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish-threads/SKILL.md
git commit -m "feat: add vp-publish-threads SKILL.md"
```

---

### Task 14: publish_ins.py

**Files:**
- Create: `skills/vp-publish-ins/publish_ins.py`
- Create: `tests/test_publish_ins.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_publish_ins.py
import os, sys, subprocess

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-ins/publish_ins.py', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-ins'))
    import publish_ins
    assert 'skills' not in publish_ins.PROFILE_BASE
    assert publish_ins.PROFILE_BASE.endswith('profile')
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_publish_ins.py -v
```

- [ ] **Step 3: 实现 publish_ins.py**

```python
# skills/vp-publish-ins/publish_ins.py
"""Instagram 自动发布脚本"""
import argparse, time, os, json

PROFILE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile"
)
ACCOUNTS_FILE = os.path.join(PROFILE_BASE, "accounts.json")


def load_profile_dir(group_name):
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError("accounts.json 不存在")
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        accounts = json.load(f)
    for i, g in enumerate(accounts):
        if g["name"] == group_name:
            subpath = g.get("platforms", {}).get("ins")
            if not subpath:
                raise ValueError(f"账号组「{group_name}」未登录 Instagram")
            return os.path.join(PROFILE_BASE, subpath)
    raise ValueError(f"账号组「{group_name}」不存在")


def clear_locks(profile_dir):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lp = os.path.join(profile_dir, lock)
        if os.path.exists(lp):
            os.remove(lp)


def format_tags(tags):
    if not tags:
        return ""
    return " ".join("#" + t.strip().lstrip("#") for t in tags.split() if t.strip())


def publish(file_path, title, description, tags, group):
    from playwright.sync_api import sync_playwright

    profile_dir = load_profile_dir(group)
    os.makedirs(profile_dir, exist_ok=True)
    clear_locks(profile_dir)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page.goto("https://www.instagram.com/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        if "accounts/login" in page.url or page.locator('input[name="username"]').count() > 0:
            print("⚠️  请在浏览器中完成 Instagram 登录...")
            page.wait_for_url("https://www.instagram.com/", timeout=120000)
            time.sleep(3)

        # 点击「创建」按钮
        try:
            create_sel = '[aria-label="New post"], [aria-label="创建"], svg[aria-label="New post"]'
            page.wait_for_selector(create_sel, timeout=15000)
            page.locator(create_sel).first.click()
            time.sleep(1)
        except Exception:
            print("⚠️  请手动点击「创建」(+) 按钮")

        # 上传文件（可选）
        if file_path:
            try:
                page.wait_for_selector('input[type="file"]', timeout=15000)
                page.locator('input[type="file"]').first.set_input_files(file_path)
                print(f"📤 文件已上传：{os.path.basename(file_path)}")
                time.sleep(4)
            except Exception:
                print("⚠️  请手动选择文件")

            # 多步骤：裁剪 → 滤镜 → Caption
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

        # 填写 Caption（title 作开头）
        try:
            caption_sel = (
                'textarea[aria-label*="caption"], textarea[placeholder*="caption"], '
                'div[aria-label*="caption"], textarea[placeholder*="Write"]'
            )
            page.wait_for_selector(caption_sel, timeout=20000)
            caption_area = page.locator(caption_sel).first
            caption_area.click()
            time.sleep(0.5)
            full_text = title
            if description:
                full_text += "\n" + description
            tag_str = format_tags(tags)
            if tag_str:
                full_text += "\n" + tag_str
            caption_area.type(full_text, delay=30)
            print("✏️  Caption 已填写")
        except Exception:
            print("⚠️  Caption 请手动填写")

        print("\n✅ 内容填写完毕！请检查后点击【分享 / Share】按钮")
        input("\n发布完成后按回车关闭浏览器...")
        context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram 自动发布")
    parser.add_argument("--file",        default="",    help="媒体文件路径（可选）")
    parser.add_argument("--title",       required=True, help="Caption 开头（必填）")
    parser.add_argument("--description", default="")
    parser.add_argument("--tags",        default="")
    parser.add_argument("--group",       required=True)
    args = parser.parse_args()
    publish(args.file or None, args.title, args.description, args.tags, args.group)
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_publish_ins.py -v
```

Expected: 全部 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/vp-publish-ins/publish_ins.py tests/test_publish_ins.py
git commit -m "feat: add publish_ins.py"
```

---

### Task 15: vp-publish-ins SKILL.md

**Files:**
- Create: `skills/vp-publish-ins/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish-ins/SKILL.md
git commit -m "feat: add vp-publish-ins SKILL.md"
```

---

### Task 16: vp-publish 编排 SKILL.md

**Files:**
- Create: `skills/vp-publish/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
pip install playwright
playwright install chromium
# 各平台完成登录：
python skills/vp-accounts/vp_accounts.py login "A组" douyin
```
```

- [ ] **Step 2: Commit**

```bash
git add skills/vp-publish/SKILL.md
git commit -m "feat: add vp-publish orchestration SKILL.md"
```

---

### Task 17: 全量测试 + Git 初始化

**Files:**
- No new files

- [ ] **Step 1: 运行所有测试**

```bash
python -m pytest tests/ -v
```

Expected: 全部 `PASSED`，共约 20 个测试

- [ ] **Step 2: 验证完整目录结构**

```bash
find skills -type f | sort
```

Expected:
```
skills/vp-accounts/SKILL.md
skills/vp-accounts/vp_accounts.py
skills/vp-publish-douyin/SKILL.md
skills/vp-publish-douyin/publish_douyin.py
skills/vp-publish-ins/SKILL.md
skills/vp-publish-ins/publish_ins.py
skills/vp-publish-shipinhao/SKILL.md
skills/vp-publish-shipinhao/publish_shipinhao.py
skills/vp-publish-threads/SKILL.md
skills/vp-publish-threads/publish_threads.py
skills/vp-publish-xhs/SKILL.md
skills/vp-publish-xhs/publish_xhs.py
skills/vp-publish/SKILL.md
```

- [ ] **Step 3: 验证 .gitignore 生效**

```bash
git status
# profile/ 不应出现在未追踪文件中
```

- [ ] **Step 4: 最终 Commit**

```bash
git add .
git commit -m "chore: complete video-pusher skills v1.0"
```

- [ ] **Step 5: 手动端到端验证（真实运行）**

```bash
# 1. 安装依赖
pip install playwright && playwright install chromium

# 2. 创建账号组
python skills/vp-accounts/vp_accounts.py add "E2E测试组"

# 3. 登录一个平台（用真实账号）
python skills/vp-accounts/vp_accounts.py login "E2E测试组" douyin

# 4. 确认登录状态
python skills/vp-accounts/vp_accounts.py status "E2E测试组" douyin ; echo $?
# Expected: 0

# 5. 发布一条测试内容（用真实视频文件）
python skills/vp-publish-douyin/publish_douyin.py \
  --file /path/to/test.mp4 \
  --title "测试发布" \
  --description "这是一条测试" \
  --tags "测试" \
  --group "E2E测试组"

# 6. 清理
python skills/vp-accounts/vp_accounts.py delete "E2E测试组"
```
