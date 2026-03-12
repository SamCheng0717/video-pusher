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
