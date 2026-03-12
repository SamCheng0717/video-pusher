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
    parser = argparse.ArgumentParser(
        prog="vp_accounts",
        description="多平台发布账号组管理工具",
        epilog="示例：\n  %(prog)s add \"A组\"\n  %(prog)s login \"A组\" douyin\n  %(prog)s list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="命令")

    sub.add_parser("list", help="列出所有账号组及各平台登录状态")

    p_add = sub.add_parser("add", help="创建新账号组")
    p_add.add_argument("name", metavar="账号组名称")

    p_del = sub.add_parser("delete", help="删除账号组")
    p_del.add_argument("name", metavar="账号组名称")

    p_login = sub.add_parser("login", help="打开浏览器登录指定平台，关闭窗口后自动保存 Session")
    p_login.add_argument("name", metavar="账号组名称")
    p_login.add_argument("platform", choices=PLATFORMS, metavar="平台", help=f"可选：{', '.join(PLATFORMS)}")

    p_status = sub.add_parser("status", help="检查登录状态（exit 0=已登录，exit 1=未登录）")
    p_status.add_argument("name", metavar="账号组名称")
    p_status.add_argument("platform", choices=PLATFORMS, metavar="平台", help=f"可选：{', '.join(PLATFORMS)}")

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
