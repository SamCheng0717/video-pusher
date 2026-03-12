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
