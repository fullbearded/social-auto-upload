# UTILS — 共享工具包

CLI 和上传器共用的基础设施工具。

## STRUCTURE

```
utils/
├── __init__.py
├── base_social_media.py    # 平台常量 + set_init_script() 注入 stealth.js
├── browser_hook.py         # 浏览器 hook 工具
├── constant.py             # 全局常量（平台枚举、分区类型 TencentZoneTypes 等）
├── files_times.py          # 定时发布时间生成（默认时间点 [6,11,14,16,22]）
├── log.py                  # loguru 日志配置（每平台独立 logger）
├── login_qrcode.py         # 二维码登录辅助
├── network.py              # 网络工具
├── stealth.min.js          # 反检测 JS（被 base_social_media.py 注入浏览器）
└── scheduler/              # 空目录（遗留，scheduler 逻辑在根目录 schedule_config.py）
```

## WHERE TO LOOK

| 任务 | 位置 |
|------|------|
| stealth.js 注入 | `base_social_media.py` → `set_init_script(context)` |
| 平台枚举常量 | `constant.py`（分区类型等） |
| 日志实例 | `log.py`（`douyin_logger`, `kuaishou_logger` 等） |
| 定时发布时间 | `files_times.py` → `generate_schedule_time_next_day()` |

## ANTI-PATTERNS

- ❌ `utils/scheduler/` 是空目录 — scheduler 逻辑在根目录 `schedule_config.py`
- ❌ 直接操作 `stealth.min.js` — 通过 `set_init_script()` 使用
- ❌ 用 `print()` 输出 — 用 `log.py` 中对应的平台 logger
