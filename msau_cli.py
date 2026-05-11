#!/usr/bin/env python3
"""
msau — 多平台多账号批量操作 CLI

用法:
  msau login <account>          # 交互式选择渠道并登录
  msau check <account>          # 检查各渠道 cookie 状态
  msau upload-video <account>   # 交互式选择渠道并批量上传视频

支持渠道: 抖音 / 小红书 / 快手 / 视频号 / Bilibili
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

from conf import BASE_DIR

# ── 渠道 → sau_cli 函数映射（延迟导入） ──────────────────────────

# 5 个用户可见渠道
SUPPORTED_CHANNELS = ["douyin", "xiaohongshu", "kuaishou", "tencent", "bilibili"]

CHANNEL_DISPLAY_NAMES = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "kuaishou": "快手",
    "tencent": "视频号",
    "bilibili": "Bilibili",
}

CHANNEL_NOTES = {
    "douyin": "手机号登录",
    "xiaohongshu": "微信扫码登录",
    "kuaishou": "快手账号登录",
    "tencent": "微信扫码登录",
    "bilibili": "Bilibili 账号登录",
}


# ── 通用工具 ────────────────────────────────────────────────────

def resolve_account_file(channel: str, account_name: str) -> Path:
    """复用 sau 的 cookie 路径格式: cookies/{channel}_{account_name}.json"""
    path = Path(BASE_DIR) / "cookies" / f"{channel}_{account_name}.json"
    path.parent.mkdir(exist_ok=True)
    return path


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    tags: list[str] = []
    for item in raw.split(","):
        cleaned = item.strip().lstrip("#")
        if cleaned:
            tags.append(cleaned)
    return tags


def parse_publish_times(time_str: str) -> list[int] | None:
    """解析发布时间字符串，支持 '9,15,20' / '9 15 20' / '9:00,15:30' 等格式"""
    times: list[int] = []
    cleaned = time_str.strip().replace("[", "").replace("]", "")
    for part in cleaned.replace(",", " ").replace("，", " ").split():
        try:
            if ":" in part:
                times.append(int(part.split(":")[0]))
            else:
                hour = int(part)
                if 0 <= hour <= 23:
                    times.append(hour)
        except ValueError:
            print(f"⚠️  无法解析时间: {part}")
    return times or None


# ── 交互式渠道选择 ───────────────────────────────────────────────

def select_channels(action_label: str = "操作") -> list[str]:
    """交互式选择渠道，返回选中的 channel key 列表"""
    print(f"\n📱 请选择要{action_label}的渠道:")
    print("   (输入编号，多个用逗号分隔)")
    print()

    for i, ch in enumerate(SUPPORTED_CHANNELS, 1):
        note = CHANNEL_NOTES.get(ch, "")
        print(f"  {i}. {CHANNEL_DISPLAY_NAMES[ch]} ({ch}) — {note}")

    print(f"\n💡 示例: 1,2,5  →  抖音+小红书+Bilibili")
    print(f"   直接回车 → 全部渠道")

    while True:
        try:
            raw = input(f"\n🔧 请选择: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n❌ 已取消")
            sys.exit(0)

        if not raw:
            print(f"✅ 已选择: 全部渠道 ({', '.join(CHANNEL_DISPLAY_NAMES[ch] for ch in SUPPORTED_CHANNELS)})")
            return SUPPORTED_CHANNELS.copy()

        try:
            indices = [int(x.strip()) for x in raw.split(",")]
            if all(1 <= idx <= len(SUPPORTED_CHANNELS) for idx in indices):
                selected = [SUPPORTED_CHANNELS[idx - 1] for idx in indices]
                names = ", ".join(CHANNEL_DISPLAY_NAMES[ch] for ch in selected)
                print(f"✅ 已选择: {names}")
                return selected
            else:
                print(f"❌ 请输入 1-{len(SUPPORTED_CHANNELS)} 之间的数字")
        except ValueError:
            print("❌ 请输入数字编号")


# ── Login ────────────────────────────────────────────────────────

async def login_account(account_name: str, channels: list[str], headless: bool = True, timeout: int = 60) -> dict:
    """对指定账号的指定渠道依次执行登录，每个渠道限时 timeout 秒"""
    results: dict[str, dict] = {}

    for ch in channels:
        account_file = resolve_account_file(ch, account_name)
        display = CHANNEL_DISPLAY_NAMES.get(ch, ch)
        print(f"\n{'=' * 50}")
        print(f"🔄 正在登录 {display} ({ch}) → {account_file.name}  [超时 {timeout}s]")
        print(f"{'=' * 50}")

        try:
            result = await asyncio.wait_for(
                _do_login(ch, str(account_file), headless=headless),
                timeout=timeout,
            )
            results[ch] = result
            if result.get("success"):
                print(f"✅ {display} 登录成功")
            else:
                msg = result.get("message", "未知错误")
                print(f"❌ {display} 登录失败: {msg}")
        except asyncio.TimeoutError:
            results[ch] = {"success": False, "message": f"登录超时 ({timeout}s)"}
            print(f"⏰ {display} 登录超时 ({timeout}s)，跳到下一个渠道")
        except Exception as exc:
            results[ch] = {"success": False, "message": str(exc)}
            print(f"❌ {display} 登录异常: {exc}")

    return results


async def _do_login(channel: str, account_file: str, headless: bool = True) -> dict:
    """根据 channel 调用对应的 setup 函数"""
    if channel == "douyin":
        from uploader.douyin_uploader.main import douyin_setup
        return await douyin_setup(account_file, handle=True, return_detail=True, headless=headless)
    elif channel in ("xiaohongshu", "xhs"):
        from uploader.xiaohongshu_uploader.main import xiaohongshu_setup
        return await xiaohongshu_setup(account_file, handle=True, return_detail=True, headless=headless)
    elif channel in ("kuaishou", "ks"):
        from uploader.ks_uploader.main import ks_setup
        return await ks_setup(account_file, handle=True, return_detail=True, headless=headless)
    elif channel == "tencent":
        from uploader.tencent_uploader.main import weixin_setup
        return await weixin_setup(account_file, handle=True, return_detail=True, headless=headless)
    elif channel == "bilibili":
        from uploader.bilibili_uploader.runtime import run_biliup_command
        result = run_biliup_command(["-u", account_file, "login"], interactive=True)
        success = result.returncode == 0
        return {
            "success": success,
            "message": (result.stderr or result.stdout or "").strip() or ("Bilibili login completed" if success else "Bilibili login failed"),
            "account_file": account_file,
        }
    else:
        return {"success": False, "message": f"不支持的渠道: {channel}"}


# ── Check ────────────────────────────────────────────────────────

async def check_account(account_name: str, channels: list[str]) -> dict[str, bool]:
    """检查指定账号各渠道的 cookie 状态"""
    results: dict[str, bool] = {}

    for ch in channels:
        account_file = resolve_account_file(ch, account_name)
        display = CHANNEL_DISPLAY_NAMES.get(ch, ch)

        try:
            valid = await _do_check(ch, account_file)
            results[ch] = valid
            status = "✅ 有效" if valid else "❌ 无效/不存在"
            print(f"  {display:8} ({ch:12}) — {status}  {account_file.name}")
        except Exception as exc:
            results[ch] = False
            print(f"  {display:8} ({ch:12}) — ❌ 检查失败: {exc}")

    return results


async def _do_check(channel: str, account_file: Path) -> bool:
    """根据 channel 调用对应的 cookie_auth 函数"""
    from utils.base_social_media import has_user_data_dir

    if not account_file.exists() and not has_user_data_dir(str(account_file)):
        return False

    if channel == "douyin":
        from uploader.douyin_uploader.main import cookie_auth as douyin_auth
        return await douyin_auth(str(account_file))
    elif channel in ("xiaohongshu", "xhs"):
        from uploader.xiaohongshu_uploader.main import cookie_auth as xhs_auth
        return await xhs_auth(str(account_file))
    elif channel in ("kuaishou", "ks"):
        from uploader.ks_uploader.main import cookie_auth as ks_auth
        return await ks_auth(str(account_file))
    elif channel == "tencent":
        from uploader.tencent_uploader.main import cookie_auth as tencent_auth
        return await tencent_auth(str(account_file))
    elif channel == "bilibili":
        from uploader.bilibili_uploader.runtime import run_biliup_command
        result = run_biliup_command(["-u", str(account_file), "renew"])
        return result.returncode == 0
    else:
        return False


# ── Upload Video ─────────────────────────────────────────────────

@dataclass(slots=True)
class MsauUploadConfig:
    """批量上传配置"""
    account_name: str
    channels: list[str]
    videos_dir: Path
    publish_times: list[int] = field(default_factory=lambda: [5, 8, 12, 17, 19])
    group_size: int = 5
    random_minutes: int = 10
    start_date: str = "tomorrow"  # "tomorrow" or "YYYY-MM-DD"
    headless: bool = True
    debug: bool = True


def _find_video_files(videos_dir: Path) -> list[Path]:
    """递归查找目录下的所有 mp4 文件"""
    if not videos_dir.exists():
        return []
    return sorted(p for p in videos_dir.rglob("*.mp4") if p.is_file())


async def upload_videos(config: MsauUploadConfig) -> None:
    """批量上传视频到选定渠道"""
    # 1. 查找视频文件
    video_files = _find_video_files(config.videos_dir)
    if not video_files:
        print(f"❌ 在 {config.videos_dir} 下没有找到 MP4 文件")
        return

    print(f"\n📹 找到 {len(video_files)} 个视频文件")
    print(f"📁 目录: {config.videos_dir}")

    # 2. 导入调度工具
    from utils.enhanced_scheduler import generate_smart_schedule, print_detailed_schedule, validate_schedule_config
    from utils.files_times import get_title_and_hashtags
    from utils.countdown import countdown_for_platform
    from utils.publish_cache import PublishCache

    # 3. 验证配置
    is_valid, message = validate_schedule_config(video_files, config.publish_times, config.start_date)
    if not is_valid:
        print(f"❌ 配置验证失败: {message}")
        return

    # 4. 生成调度计划
    try:
        publish_datetimes, schedule = generate_smart_schedule(
            video_files=video_files,
            publish_times=config.publish_times,
            start_date_str=config.start_date,
            group_size=config.group_size,
            random_minutes=config.random_minutes,
        )
    except Exception as exc:
        print(f"❌ 调度计划生成失败: {exc}")
        return

    # 5. 显示并确认计划
    print(f"\n📊 调度计划已生成:")
    print(f"   📅 开始日期: {schedule.get('start_date')}")
    print(f"   📹 视频总数: {len(video_files)}")
    print(f"   📊 发布天数: {schedule.get('total_days', 0)}")

    if not print_detailed_schedule(publish_datetimes, schedule, video_files):
        print("❌ 已取消")
        return

    # 6. 逐渠道执行上传
    publish_cache = PublishCache()

    for ch in config.channels:
        print(f"\n{'=' * 60}")
        print(f"📱 {CHANNEL_DISPLAY_NAMES.get(ch, ch)} ({ch}) — 开始上传")
        print(f"{'=' * 60}")

        account_file = resolve_account_file(ch, config.account_name)

        # 验证 cookie
        is_ready = await _do_setup(ch, str(account_file), headless=config.headless)
        if not is_ready:
            print(f"❌ {CHANNEL_DISPLAY_NAMES.get(ch, ch)} 认证失败，跳过")
            continue

        print(f"✅ {CHANNEL_DISPLAY_NAMES.get(ch, ch)} 认证成功")

        # 执行上传
        success_count, fail_count, skip_count = 0, 0, 0

        for idx, video in enumerate(video_files):
            if idx >= len(publish_datetimes):
                break

            video_path = str(video)
            publish_time = publish_datetimes[idx]

            # 检查缓存
            if publish_cache.is_video_published(ch, video_path):
                print(f"  ⏭️  [{idx + 1}/{len(video_files)}] {video.name} — 已发布，跳过")
                skip_count += 1
                continue

            try:
                title, tags = get_title_and_hashtags(video_path)
                thumbnail = _find_thumbnail(video)

                print(f"\n  📹 [{idx + 1}/{len(video_files)}] {video.name}")
                print(f"     标题: {title}")
                print(f"     标签: {tags}")
                print(f"     发布时间: {publish_time.strftime('%Y-%m-%d %H:%M')}")

                result = await _do_upload_single(
                    channel=ch,
                    account_file=str(account_file),
                    video_file=video,
                    title=title,
                    description="",
                    tags=tags,
                    publish_time=publish_time,
                    thumbnail_path=thumbnail,
                    headless=config.headless,
                    debug=config.debug,
                )

                if result:
                    success_count += 1
                    publish_cache.mark_video_published(ch, video_path, publish_time)
                    print(f"     ✅ 上传成功")
                else:
                    fail_count += 1
                    publish_cache.mark_video_failed(ch, video_path, publish_time, "上传失败")
                    print(f"     ❌ 上传失败")

                # 上传间隔
                if idx < len(video_files) - 1:
                    delay = random.randint(20, 60)
                    await countdown_for_platform(ch, delay)

            except Exception as exc:
                fail_count += 1
                err_msg = str(exc)[:500]
                publish_cache.mark_video_failed(ch, video_path, publish_time, err_msg)
                print(f"     ❌ 异常: {err_msg}")

        # 渠道统计
        total = success_count + fail_count
        rate = f"{(success_count / total * 100):.1f}%" if total > 0 else "N/A"
        print(f"\n📈 {CHANNEL_DISPLAY_NAMES.get(ch, ch)} 上传完成:")
        print(f"   ✅ 成功: {success_count}  ❌ 失败: {fail_count}  ⏭️ 跳过: {skip_count}")
        print(f"   📊 成功率: {rate}")


async def _do_setup(channel: str, account_file: str, headless: bool = True) -> bool:
    """调用对应渠道的 setup 函数验证 cookie"""
    if channel == "douyin":
        from uploader.douyin_uploader.main import douyin_setup
        return await douyin_setup(account_file, handle=False, headless=headless)
    elif channel in ("xiaohongshu", "xhs"):
        from uploader.xiaohongshu_uploader.main import xiaohongshu_setup
        return await xiaohongshu_setup(account_file, handle=False, headless=headless)
    elif channel in ("kuaishou", "ks"):
        from uploader.ks_uploader.main import ks_setup
        return await ks_setup(account_file, handle=False, headless=headless)
    elif channel == "tencent":
        from uploader.tencent_uploader.main import weixin_setup
        return await weixin_setup(account_file, handle=False, headless=headless)
    elif channel == "bilibili":
        return Path(account_file).exists()
    return False


async def _do_upload_single(
    channel: str,
    account_file: str,
    video_file: Path,
    title: str,
    description: str,
    tags: str,
    publish_time: datetime,
    thumbnail_path: str | None = None,
    headless: bool = True,
    debug: bool = True,
) -> bool:
    """调用对应渠道的上传器上传单个视频"""
    if channel == "douyin":
        from uploader.douyin_uploader.main import DouYinVideo
        app = DouYinVideo(
            title, str(video_file), tags, publish_time, account_file,
            desc=description,
            thumbnail_portrait_path=thumbnail_path,
            publish_strategy="scheduled",
            debug=debug, headless=headless,
        )
        await app.douyin_upload_video()
        return True

    elif channel in ("xiaohongshu", "xhs"):
        from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
        app = XiaoHongShuVideo(
            title, str(video_file), description, tags, publish_time, account_file,
            thumbnail_path=thumbnail_path,
            publish_strategy="scheduled",
            debug=debug, headless=headless,
        )
        await app.main()
        return True

    elif channel in ("kuaishou", "ks"):
        from uploader.ks_uploader.main import KSVideo
        app = KSVideo(
            title=title, file_path=str(video_file), desc=description,
            tags=tags, publish_date=publish_time, account_file=account_file,
            thumbnail_path=thumbnail_path,
            publish_strategy="scheduled",
            debug=debug, headless=headless,
        )
        await app.main()
        return True

    elif channel == "tencent":
        from uploader.tencent_uploader.main import TencentVideo
        kwargs = dict(
            title=title, file_path=str(video_file), tags=tags,
            publish_date=publish_time, account_file=account_file,
            debug=debug, headless=headless,
        )
        if thumbnail_path:
            kwargs["thumbnail_path"] = thumbnail_path
        app = TencentVideo(**kwargs)
        await app.main()
        return True

    elif channel == "bilibili":
        from uploader.bilibili_uploader.runtime import run_biliup_command
        args = ["-u", account_file, "upload", str(video_file),
                "--title", title, "--desc", description]
        result = run_biliup_command(args)
        return result.returncode == 0

    return False


def _find_thumbnail(video_path: Path) -> str | None:
    """查找视频对应的封面图"""
    candidates = [
        video_path.with_suffix(".jpg"),
        video_path.with_suffix(".png"),
        video_path.with_suffix(".jpeg"),
        video_path.parent / f"{video_path.stem}_thumbnail.jpg",
        video_path.parent / f"{video_path.stem}_thumbnail.png",
        video_path.parent / f"{video_path.stem}_cover.jpg",
        video_path.parent / f"{video_path.stem}_cover.png",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


# ── CLI Parser & Dispatch ────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msau",
        description="多平台多账号批量操作 CLI (Multi-platform Social Auto Upload)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  msau login phone1                       # 交互式选择渠道并登录 phone1 账号
  msau login phone1 -c douyin,bilibili    # 直接指定渠道登录
  msau check phone1                       # 检查 phone1 各渠道 cookie 状态
  msau check phone1 -c douyin,xiaohongshu # 检查指定渠道
  msau upload-video phone1                # 交互式选择渠道并批量上传
  msau upload-video phone1 -c douyin      # 只上传到抖音
  msau upload-video phone1 --times 9,15,20 --videos-dir ./my_videos
        """,
    )

    sub = parser.add_subparsers(dest="action", help="操作类型")

    # ── login ──
    p_login = sub.add_parser("login", help="登录指定账号的渠道")
    p_login.add_argument("account", help="账号名称 (如 phone1)")
    p_login.add_argument("-c", "--channels", help="渠道列表 (逗号分隔，如 douyin,bilibili)")
    p_login.add_argument("--timeout", "-T", type=int, default=60, help="每个渠道登录超时秒数 (默认: 60)")
    p_login.add_argument("--headless", action="store_true", default=True, help="无头模式 (默认)")
    p_login.add_argument("--no-headless", action="store_false", dest="headless", help="显示浏览器")

    # ── check ──
    p_check = sub.add_parser("check", help="检查指定账号的 cookie 状态")
    p_check.add_argument("account", help="账号名称")
    p_check.add_argument("-c", "--channels", help="渠道列表 (逗号分隔)")

    # ── upload-video ──
    p_upload = sub.add_parser("upload-video", help="批量上传视频到指定渠道")
    p_upload.add_argument("account", help="账号名称")
    p_upload.add_argument("-c", "--channels", help="渠道列表 (逗号分隔)")
    p_upload.add_argument("--videos-dir", type=Path, default=Path(BASE_DIR) / "videos", help="视频目录 (默认: ./videos)")
    p_upload.add_argument("--times", "-t", help="发布时间，如 '9,15,20' (默认: 5,8,12,17,19)")
    p_upload.add_argument("--group-size", "-g", type=int, default=5, help="每日分组大小 (默认: 5)")
    p_upload.add_argument("--random-minutes", "-r", type=int, default=10, help="随机偏移分钟 (默认: 10)")
    p_upload.add_argument("--start-date", "-d", help="开始日期 YYYY-MM-DD (默认: 明天)")
    p_upload.add_argument("--headless", action="store_true", default=True)
    p_upload.add_argument("--no-headless", action="store_false", dest="headless")
    p_upload.add_argument("--debug", action="store_true", default=True)
    p_upload.add_argument("--no-debug", action="store_false", dest="debug")

    return parser


def _parse_channels_arg(channels_str: str | None) -> list[str] | None:
    """解析 -c 参数，返回 channel key 列表。未知渠道忽略。"""
    if not channels_str:
        return None
    result: list[str] = []
    for part in channels_str.split(","):
        ch = part.strip().lower()
        if ch in SUPPORTED_CHANNELS:
            result.append(ch)
        elif ch == "xhs":
            result.append("xiaohongshu")
        elif ch == "ks":
            result.append("kuaishou")
        elif ch in ("视频号", "shipinhao"):
            result.append("tencent")
        else:
            print(f"⚠️  未知渠道: {ch}，已忽略")
    return result


async def dispatch(args: argparse.Namespace) -> int:
    """路由到对应操作"""
    if not args.action:
        build_parser().print_help()
        return 0

    account = args.account

    # 解析渠道
    channels = _parse_channels_arg(getattr(args, "channels", None))
    if channels is None:
        channels = select_channels(
            "登录" if args.action == "login" else
            "检查" if args.action == "check" else
            "上传视频"
        )

    if not channels:
        print("❌ 没有选择任何渠道")
        return 1

    # 显示操作摘要
    channel_names = ", ".join(CHANNEL_DISPLAY_NAMES.get(ch, ch) for ch in channels)
    print(f"\n{'=' * 60}")
    print(f"👤 账号: {account}")
    print(f"📱 渠道: {channel_names}")
    print(f"🔧 操作: {args.action}")
    print(f"{'=' * 60}")

    if args.action == "login":
        results = await login_account(account, channels, headless=args.headless, timeout=args.timeout)
        print(f"\n{'=' * 60}")
        print("📊 登录结果汇总")
        print(f"{'=' * 60}")
        for ch, result in results.items():
            status = "✅ 成功" if result.get("success") else "❌ 失败"
            msg = result.get("message", "")
            print(f"  {CHANNEL_DISPLAY_NAMES.get(ch, ch):8} — {status}  {msg}")
        success_count = sum(1 for r in results.values() if r.get("success"))
        print(f"\n📈 总计: {success_count}/{len(results)} 成功")
        return 0 if success_count == len(results) else 1

    elif args.action == "check":
        results = await check_account(account, channels)
        print(f"\n{'=' * 60}")
        print(f"📊 账号 {account} Cookie 状态")
        print(f"{'=' * 60}")
        valid_count = sum(1 for v in results.values() if v)
        print(f"\n📈 总计: {valid_count}/{len(results)} 有效")
        return 0 if valid_count == len(results) else 1

    elif args.action == "upload-video":
        import re

        default_videos_dir = getattr(args, "videos_dir", None) or Path(BASE_DIR) / "videos"
        default_times = [5, 8, 12, 17, 19]
        default_random = 10
        default_start = "tomorrow"

        print(f"\n{'─' * 50}")
        print(f"📋 上传配置（直接回车使用默认值）")
        print(f"{'─' * 50}")

        while True:
            try:
                raw = input(f"📁 视频目录 [{default_videos_dir}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ 已取消")
                return 1
            if not raw:
                videos_dir = default_videos_dir
                break
            candidate = Path(raw).expanduser().resolve()
            if candidate.is_dir():
                videos_dir = candidate
                break
            print(f"❌ 目录不存在: {raw}")

        while True:
            try:
                raw = input(f"⏰ 发布时间（逗号分隔小时数） [{','.join(map(str, default_times))}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ 已取消")
                return 1
            if not raw:
                publish_times = default_times
                break
            parsed = parse_publish_times(raw)
            if parsed:
                publish_times = parsed
                break
            print(f"❌ 无法解析，请输入如 9,15,20 的格式")

        while True:
            try:
                raw = input(f"🎲 随机偏移（分钟） [{default_random}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ 已取消")
                return 1
            if not raw:
                random_minutes = default_random
                break
            try:
                random_minutes = int(raw)
                if random_minutes >= 0:
                    break
                print(f"❌ 请输入非负整数")
            except ValueError:
                print(f"❌ 请输入整数")

        while True:
            try:
                raw = input(f"📅 开始日期（YYYY-MM-DD，或 'tomorrow'） [{default_start}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ 已取消")
                return 1
            if not raw:
                start_date = default_start
                break
            if raw.lower() == "tomorrow":
                start_date = "tomorrow"
                break
            if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
                start_date = raw
                break
            print(f"❌ 格式错误，请输入 YYYY-MM-DD 或 tomorrow")

        config = MsauUploadConfig(
            account_name=account,
            channels=channels,
            videos_dir=videos_dir,
            publish_times=publish_times,
            group_size=args.group_size,
            random_minutes=random_minutes,
            start_date=start_date,
            headless=args.headless,
            debug=args.debug,
        )

        await upload_videos(config)
        return 0

    else:
        print(f"❌ 未知操作: {args.action}")
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return asyncio.run(dispatch(args))
    except KeyboardInterrupt:
        print("\n❌ 已取消")
        return 130
    except Exception as exc:
        print(f"❌ 错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
