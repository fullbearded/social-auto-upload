# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-08
**Commit:** 8c30f4c
**Branch:** main

## OVERVIEW

自动化视频/图文发布工具。Python CLI + Flask Web 后端 + Vue 前端，通过 patchright（playwright 隐蔽版）浏览器自动化驱动 8+ 平台上传。

## STRUCTURE

```
.
├── sau_cli.py              # CLI 入口 `sau` 命令
├── sau_backend.py          # Flask Web 后端 (端口 5409)
├── conf.py                 # 运行时配置（从 conf.example.py 复制）
├── uploader/               # 各平台上传器（8个子包）
├── utils/                  # CLI/上传器共享工具（stealth注入、常量、日志）
├── myUtils/                # Web后端专用工具（登录、发布、鉴权）
├── sau_frontend/           # Vue 3 前端（独立子项目）
├── skills/                 # AI Agent Skill 定义（Claude Code / OpenClaw 用）
├── examples/               # 历史示例脚本（非主线，参考值低）
├── tests/                  # 单元测试（pytest + unittest）
├── db/                     # SQLite 数据库初始化
├── cookies/                # CLI 用 cookie 存储（{platform}_{account}.json）
└── cookiesFile/            # Web 后端用 cookie 存储
```

## WHERE TO LOOK

| 任务 | 位置 | 备注 |
|------|------|------|
| 新增平台上传器 | `uploader/douyin_uploader/` | 以抖音为模板，复制后改名 |
| 修改上传逻辑 | `uploader/{platform}_uploader/main.py` | 每平台一个 main.py |
| 登录/cookie 流程 | `sau_cli.py` 的 login 子命令 | CLI 主线 |
| Web 后端登录 | `myUtils/login.py` | 旧版，用 playwright 非 patchright |
| 前端页面 | `sau_frontend/src/views/` | 5 个页面组件 |
| AI Agent Skill | `skills/{platform}-upload/SKILL.md` | 含 CLI 契约和参考文档 |
| 全局常量 | `utils/constant.py` | 平台枚举、分区类型 |
| 浏览器反检测 | `utils/base_social_media.py` | `set_init_script()` 注入 stealth.js |
| CLI 参数定义 | `sau_cli.py` | argparse 子命令树 |

## CONVENTIONS

- **Python >=3.10,<3.13**，包管理用 `uv`，`requirements.txt` 仅历史兼容
- **浏览器自动化**：主线用 `patchright`（非 `playwright`）
- **日志**：`loguru`，每平台独立 logger，从 `utils/log.py` 导入
- **路径**：`pathlib.Path`，禁止字符串拼接
- **uploader 继承**：`BaseVideoUploader` → `{Platform}BaseUploader` → `{Platform}Video` / `{Platform}Note`
- **上传后必须** `await context.storage_state(path=account_file)` 刷新 cookie
- **每次创建 context 必须** `set_init_script(context)` 注入 stealth.js
- **CLI 入口**：`sau <platform> <action> --account <name>`
- **平台类型 ID**：1=小红书, 2=视频号, 3=抖音, 4=快手

## ANTI-PATTERNS (THIS PROJECT)

- ❌ `myUtils/` 用 `playwright` 和 `print()` — 旧版遗留，新代码不要跟随
- ❌ `examples/` 直连 uploader — 历史脚本，新功能走 CLI
- ❌ 跳过 `set_init_script()` — 会被平台检测
- ❌ 上传后不刷新 cookie — cookie 会过期
- ❌ 字符串拼接路径 — 用 `pathlib.Path`
- ❌ 裸 `print()` — 用平台 logger
- ❌ 定时发布 ≤ 当前时间 + 2小时 — `validate_publish_date()` 会抛异常
- ❌ 前端用 HTML5 History 路由 — 固定 `createWebHashHistory()`
- ❌ 前端直接用 `axios` — 通过 `src/utils/request.js` 的 `http` 封装

## UNIQUE STYLES

- **两套小红书并存**：`xiaohongshu_uploader/`（主线浏览器版）vs `xhs_uploader/`（旧版API版）
- **两套 cookie 目录**：`cookies/`（CLI）vs `cookiesFile/`（Web后端）
- **Bilibili 特殊**：不直接自动化，封装 `biliup` 二进制工具（`bilibili_uploader/runtime.py`）
- **TikTok 双实现**：`tk_uploader/main.py`（Playwright）+ `main_chrome.py`（Chrome版）
- **`_msg(emoji, text)`**：各 uploader 本地日志格式化辅助函数
- **skill 体系**：`skills/` 目录下的 SKILL.md 供 AI Agent 使用，定义 CLI 契约

## COMMANDS

```bash
# 后端安装
uv sync                                    # 基础依赖
uv sync --extra web                        # 含 Flask
uv run patchright install chromium         # 浏览器驱动

# 运行
uv run sau <platform> <action> [opts]      # CLI
uv run python sau_backend.py               # Web 后端 :5409

# 前端（sau_frontend/ 目录下）
npm install && npm run dev                 # 开发 :5173
npm run build                             # 生产构建

# 测试
uv run pytest tests/                       # 只跑 tests/（根目录遗留脚本有问题）
```

## NOTES

- 无 CI/CD 流水线
- `conf.py` 必须从 `conf.example.py` 复制后配置
- `utils/scheduler/` 是空目录，scheduler 逻辑在根目录 `schedule_config.py`
- 根目录有 2 个遗留测试文件（`test_interactive_config.py`, `test_scheduler_args.py`），不属于 tests/
- 抖音标题最多 30 字符，快手标签最多 3 个
- 快手需处理 Joyride 引导遮罩（`close_guide_overlay()`）
