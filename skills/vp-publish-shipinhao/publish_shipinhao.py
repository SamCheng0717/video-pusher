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
    parser = argparse.ArgumentParser(
        description="微信视频号自动发布 —— 标题拼入正文开头，登录需微信扫码，需手动点击发表",
        epilog="示例：\n  %(prog)s --file video.mp4 --title \"标题\" --group \"A组\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file",        required=True,  help="视频文件路径，必填")
    parser.add_argument("--title",       required=True,  help="标题（拼入正文开头，视频号无独立标题字段），必填")
    parser.add_argument("--description", default="",     help="正文内容，选填")
    parser.add_argument("--tags",        default="",     help="标签，空格分隔，自动添加 # 前缀，选填")
    parser.add_argument("--group",       required=True,  help="账号组名称，必须已通过 vp-accounts 完成登录")
    args = parser.parse_args()
    publish(args.file, args.title, args.description, args.tags, args.group)
