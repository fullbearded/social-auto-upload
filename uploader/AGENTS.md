# UPLOADER 模块

8 个平台上传器子包，每个子包独立实现一个平台的视频/图文上传。

## STRUCTURE

```
uploader/
├── base_video.py           # BaseVideoUploader 基类（所有平台继承）
├── __init__.py
├── douyin_uploader/        # 抖音 ✅ CLI 已接入（参考模板）
├── ks_uploader/            # 快手 ✅ CLI 已接入
├── xiaohongshu_uploader/   # 小红书（主线浏览器版）✅ CLI 已接入
├── bilibili_uploader/      # B站 ✅ CLI 已接入（封装 biliup 二进制）
├── xhs_uploader/           # 小红书（旧版 API 版）❌ 未接入 CLI
├── tencent_uploader/       # 视频号 ❌ 未接入 CLI
├── baijiahao_uploader/     # 百家号 ❌ 未接入 CLI
└── tk_uploader/            # TikTok ❌ 未接入 CLI（有双实现）
```

## WHERE TO LOOK

| 任务 | 位置 |
|------|------|
| 新增平台 | 复制 `douyin_uploader/`，改平台名和常量 |
| 基类验证逻辑 | `base_video.py` 的 `validate_*` 方法 |
| CLI 接入新平台 | `sau_cli.py` 添加 argparse 子命令 |
| Bilibili 特殊逻辑 | `bilibili_uploader/runtime.py`（二进制管理） |

## CONVENTIONS

- **继承链**：`BaseVideoUploader` → `{Platform}BaseUploader` → `{Platform}Video` / `{Platform}Note`
- **构造参数**：`title, file_path, tags, publish_date, account_file` + 可选 `desc, thumbnail_path, publish_strategy, debug, headless`
- **必须调用顺序**：`validate_upload_args()` → `validate_base_args()` → 父类 `validate_video_file()` / `validate_image_file()` / `validate_publish_date()`
- **上传入口**：`async def upload(self, playwright: Playwright)` + `async def main(self)` 包装 `async_playwright()`
- **cookie 刷新**：上传成功后必须 `await context.storage_state(path=self.account_file)`
- **stealth 注入**：每次创建 context 后必须 `set_init_script(context)`
- **日志**：每个 uploader 用本地 `_msg(emoji, text)` 辅助函数格式化消息
- **发布策略**：`publish_date = 0` 表示立即发布；`datetime` 对象表示定时；常量命名 `{PLATFORM}_PUBLISH_STRATEGY_*`
- **浏览器启动**：优先 `LOCAL_CHROME_PATH`，否则 `channel="chrome"`

## ANTI-PATTERNS

- ❌ 用 `douyin_uploader/` 以外的 uploader 做参考模板
- ❌ 跳过 `validate_upload_args()` / `validate_base_args()` 调用链
- ❌ 忘记 `storage_state()` 刷新 cookie
- ❌ 忘记 `set_init_script()` 注入 stealth
- ❌ 新代码参考 `xhs_uploader/`（旧版）而非 `xiaohongshu_uploader/`（主线）

## PLATFORM-SPECIFIC

| 平台 | 限制 | 注意事项 |
|------|------|----------|
| 抖音 | 标题 ≤30 字符，图文 ≤35 张 | 发布页有两个版本 URL，需同时等待 |
| 快手 | 标签最多 3 个 | 必须处理 Joyride 引导遮罩 `close_guide_overlay()` |
| Bilibili | — | 不直接自动化，通过 `biliup` 二进制工具 |
| TikTok | — | 双实现：`main.py`（Playwright）+ `main_chrome.py`（Chrome） |
| 小红书 | — | 两套并存，主线是 `xiaohongshu_uploader/` |
