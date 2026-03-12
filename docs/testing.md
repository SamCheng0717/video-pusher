# 测试指南

## 第一层：自动化单元测试

无需浏览器，约 30 秒。

```bash
uv run pytest tests/ -v
```

**预期结果：** 24 passed，0 failed

---

## 第二层：CLI 冒烟测试

无需浏览器，约 5 分钟。逐条执行，验证预期输出。

```bash
# 1. 查看帮助
uv run python skills/vp-accounts/vp_accounts.py --help
# 预期：显示 list / add / delete / login / status 子命令

# 2. 空列表
uv run python skills/vp-accounts/vp_accounts.py list
# 预期：[]

# 3. 创建账号组
uv run python skills/vp-accounts/vp_accounts.py add "测试组"
# 预期：✅ 账号组「测试组」已创建

# 4. 重复创建（应失败）
uv run python skills/vp-accounts/vp_accounts.py add "测试组"
# 预期：exit code 1，stderr 输出"已存在"

# 5. 查看列表
uv run python skills/vp-accounts/vp_accounts.py list
# 预期：[{"name": "测试组", "platforms": {"douyin": false, "xhs": false, ...}}]

# 6. 未登录状态检查（应失败）
uv run python skills/vp-accounts/vp_accounts.py status "测试组" douyin ; echo "exit: $?"
# 预期：exit: 1

# 7. 发布脚本缺少必填参数（应失败）
uv run python skills/vp-publish-douyin/publish_douyin.py --group "测试组"
# 预期：exit code 2，stderr 提示 --file 和 --title 必填

uv run python skills/vp-publish-threads/publish_threads.py --group "测试组"
# 预期：exit code 2，stderr 提示 --title 必填

# 8. 清理
uv run python skills/vp-accounts/vp_accounts.py delete "测试组"
# 预期：✅ 账号组「测试组」已删除

uv run python skills/vp-accounts/vp_accounts.py list
# 预期：[]
```

---

## 第三层：浏览器集成测试

需要真实账号，每个平台约 5 分钟。

### 准备

```bash
uv run python skills/vp-accounts/vp_accounts.py add "E2E组"
```

### 各平台登录验证

```bash
# 登录（浏览器打开后完成登录，关闭窗口即自动保存）
uv run python skills/vp-accounts/vp_accounts.py login "E2E组" douyin

# 验证 Session 已保存
uv run python skills/vp-accounts/vp_accounts.py status "E2E组" douyin ; echo "exit: $?"
# 预期：exit: 0

# 查看所有平台状态
uv run python skills/vp-accounts/vp_accounts.py list
# 预期：douyin 显示 true，其他平台仍 false
```

对每个平台（`douyin` / `xhs` / `shipinhao` / `threads` / `ins`）重复以上步骤。

### 发布测试

准备一个测试视频文件（任意 mp4），逐平台执行：

**抖音**
```bash
uv run python skills/vp-publish-douyin/publish_douyin.py \
  --file /path/to/test.mp4 \
  --title "测试发布" \
  --tags "测试" \
  --group "E2E组"
```

**小红书**
```bash
uv run python skills/vp-publish-xhs/publish_xhs.py \
  --file /path/to/test.mp4 \
  --title "测试发布" \
  --tags "测试" \
  --group "E2E组"
```

**视频号**
```bash
uv run python skills/vp-publish-shipinhao/publish_shipinhao.py \
  --file /path/to/test.mp4 \
  --title "测试发布" \
  --group "E2E组"
```

**Threads（纯文字，不需要视频）**
```bash
uv run python skills/vp-publish-threads/publish_threads.py \
  --title "测试发布" \
  --tags "测试" \
  --group "E2E组"
```

**Instagram**
```bash
uv run python skills/vp-publish-ins/publish_ins.py \
  --file /path/to/test.jpg \
  --title "测试发布" \
  --group "E2E组"
```

### 每个平台的预期结果

| 步骤 | 预期 |
|------|------|
| 浏览器打开 | 直接进入发布页（无需重新登录） |
| 文件上传 | 终端显示 `📤 正在上传：test.mp4` |
| 内容填写 | 标题、正文、标签自动填入 |
| 等待确认 | 终端显示 `✅ 内容填写完毕！` 并暂停 |
| 按回车后 | 浏览器关闭，脚本退出 |

### 平台特殊注意点

| 平台 | 注意 |
|------|------|
| 小红书 | 视频文件时自动点击"发布视频"切换模式 |
| 视频号 | 标题拼入正文开头，页面无单独标题输入框 |
| Threads | `--file` 不传时正常运行（支持纯文字发布） |
| Instagram | 上传后自动点击 Next/下一步 2-3 次到达 Caption 页 |

### 清理

```bash
uv run python skills/vp-accounts/vp_accounts.py delete "E2E组"
```

---

## 建议执行顺序

1. **第一层**（必须）：确认代码无语法错误
2. **第二层**（必须）：确认 CLI 参数和账号管理逻辑正确
3. **第三层**（选做）：选一个有账号的平台做端到端验证即可
