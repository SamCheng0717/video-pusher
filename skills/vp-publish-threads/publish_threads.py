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
    parser = argparse.ArgumentParser(
        description="Threads 自动发布 —— 支持纯文字或带媒体发布，需手动点击发帖",
        epilog="示例：\n  %(prog)s --title \"正文内容\" --group \"A组\"\n  %(prog)s --file photo.jpg --title \"正文内容\" --group \"A组\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file",        default="",    help="图片或视频文件路径，选填（不填则纯文字发布）")
    parser.add_argument("--title",       required=True, help="帖子正文开头，必填")
    parser.add_argument("--description", default="",    help="正文补充内容，选填")
    parser.add_argument("--tags",        default="",    help="标签，空格分隔，自动添加 # 前缀，选填")
    parser.add_argument("--group",       required=True, help="账号组名称，必须已通过 vp-accounts 完成登录")
    args = parser.parse_args()
    publish(args.file or None, args.title, args.description, args.tags, args.group)
