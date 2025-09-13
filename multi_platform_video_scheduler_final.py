#!/usr/bin/env python3
"""
多平台智能视频调度发布器 - 最终修复版
修复调试信息，支持自定义视频目录
精简至180行
"""

import asyncio, sys, os, random
from datetime import datetime

# Windows系统编码处理
if sys.platform == 'win32': os.system('chcp 65001')

from pathlib import Path
from utils.files_times import get_title_and_hashtags
from utils.scheduler_utils import generate_advanced_schedule, validate_video_schedule
from utils.tencent_risk_control import TencentRiskController
from utils.countdown import countdown_for_platform

# 工具类
from utils.scheduler.platform_manager import PlatformManager
from utils.scheduler.upload_engine import UploadEngine
from utils.scheduler.file_manager import FileManager
from utils.scheduler.ui_manager import UIManager
from utils.scheduler.config_manager import ConfigManager


class VideoSchedulerFinal:
    """最终修复版视频调度器"""

    def __init__(self):
        self.config = ConfigManager.create_scheduler_config()
        self.platforms = []
        self.video_files = []
        self.schedule = {}
        self.publish_datetimes = []

    def run(self):
        """运行完整调度流程"""
        try:
            UIManager.print_scheduler_header()

            # 1. 选择平台
            self.platforms = UIManager.select_platforms()

            # 2. 选择视频目录（支持自定义）
            videos_dir = self._select_videos_directory()
            self.video_files = FileManager.find_video_files(videos_dir)

            if not self.video_files:
                print("❌ 没有找到MP4视频文件")
                return

            # 3. 验证和显示配置
            if not validate_video_schedule(self.video_files, self.config['publish_times']):
                return

            UIManager.print_video_count(len(self.video_files))
            UIManager.print_config_preview(
                self.platforms,
                self.config['publish_times'],
                self.config['group_size'],
                PlatformManager.get_all_platforms()
            )

            # 4. 创建调度计划
            if not self._create_schedule():
                return

            # 5. 用户确认
            if not UIManager.get_user_confirmation():
                print("❌ 发布取消")
                return

            # 6. 执行发布
            self._execute_publishing()

            # 7. 最终统计
            UIManager.print_final_completion_stats(
                len(self.video_files),
                self.schedule,
                PlatformManager.get_all_platforms()
            )

        except KeyboardInterrupt:
            print("\n❌ 用户取消")
        except Exception as e:
            print(f"\n❌ 运行错误: {e}")

    def _select_videos_directory(self):
        """选择视频目录，支持自定义"""
        videos_dir = FileManager.get_videos_directory()

        print(f"\n📁 视频目录设置")
        print(f"   默认路径: {videos_dir}")

        try:
            custom_dir = input("自定义视频目录路径（回车使用默认）: ").strip()
            if custom_dir:
                custom_path = Path(custom_dir)
                if custom_path.exists() and custom_path.is_dir():
                    videos_dir = custom_path
                    print(f"   ✅ 使用自定义目录: {videos_dir}")
                else:
                    print(f"   ❌ 路径无效，使用默认目录: {videos_dir}")
        except:
            print(f"   ⚠️ 使用默认目录: {videos_dir}")

        return videos_dir

    def _create_schedule(self):
        """创建智能调度计划"""
        try:
            self.publish_datetimes, self.schedule = generate_advanced_schedule(
                self.video_files,
                self.config['publish_times'],
                self.config['group_size'],
                self.config['start_days'],
                timestamps=False,
                random_minutes=self.config['random_minutes']
            )

            # 显示计划摘要
            print(f"\n📊 智能调度计划已生成")
            print(f"   视频总数: {len(self.video_files)}")
            print(f"   发布天数: {self.schedule.get('total_days', 0)}")
            print(f"   每日时段数: {len(self.config['publish_times'])}")

            remainder = len(self.schedule.get('remainder_videos', []))
            if remainder > 0:
                print(f"   余数处理: {remainder}个视频")

            return True
        except Exception as e:
            print(f"❌ 调度计划生成失败: {e}")
            return False

    def _execute_publishing(self):
        """执行多平台发布"""
        UIManager.print_start_message()

        for platform in self.platforms:
            self._publish_single_platform(platform)

    def _publish_single_platform(self, platform):
        """发布到指定平台"""
        print(f"\n{'=' * 50}")
        print(f"📱 {platform.upper()} 平台")
        print(f"{'=' * 50}")

        # 设置平台认证
        engine = UploadEngine(platform)
        if not asyncio.run(engine.setup_platform_cookies(handle=False)):
            print(f"❌ {platform} 认证失败，跳过")
            return

        print(f"✅ {platform} 认证成功")

        # 腾讯风控处理
        risk = None
        # if platform == 'tencent':
        #     account_type = UIManager.get_tencent_account_type()
        #     risk = TencentRiskController(account_type)

        # 执行批量上传
        async def _upload_all_videos():
            success, fail = 0, 0

            for idx, video in enumerate(self.schedule.get('shuffled_order', self.video_files)):
                if idx >= len(self.publish_datetimes):
                    break

                try:
                    title, tags = get_title_and_hashtags(str(video))

                    # 智能封面图检测 - 支持多种格式
                    thumbnail_path = None
                    video_path = Path(video)
                    possible_thumbnails = [
                        video_path.with_suffix('.jpg'),
                        video_path.with_suffix('.png'),
                        video_path.with_suffix('.jpeg'),
                        video_path.parent / f"{video_path.stem}_thumbnail.jpg",
                        video_path.parent / f"{video_path.stem}_thumbnail.png",
                        video_path.parent / f"{video_path.stem}_cover.jpg",
                        video_path.parent / f"{video_path.stem}_cover.png"
                    ]

                    for thumb_path in possible_thumbnails:
                        if thumb_path.exists():
                            thumbnail_path = str(thumb_path)
                            break

                    # 打印视频信息
                    print(f"视频文件名：{video}")
                    print(f"标题：{title}")
                    print(f"Hashtag：{tags}")
                    if thumbnail_path:
                        print(f"封面路径：{thumbnail_path}")
                    else:
                        print("封面路径：无封面图（使用平台默认）")

                    result = await UploadEngine.upload_video_to_platform(
                        platform=platform,
                        video_file=video,
                        title=title,
                        tags=tags,
                        publish_time=self.publish_datetimes[idx],
                        video_info={'global_index': idx, 'thumbnail_path': thumbnail_path},
                        risk_controller=risk
                    )

                    if result:
                        success += 1
                        print(f"✅ [{idx + 1}/{len(self.video_files)}] {video.name}")
                    else:
                        fail += 1
                        print(f"❌ [{idx + 1}/{len(self.video_files)}] {video.name}")

                    if idx < len(self.video_files) - 1:
                        delay = random.randint(20, 60)
                        await countdown_for_platform(platform, delay)

                except Exception as e:
                    fail += 1
                    print(f"❌ [{idx + 1}/{len(self.video_files)}] 处理失败: {e}")

            return success, fail

        success_count, fail_count = asyncio.run(_upload_all_videos())

        # 平台统计
        print(f"\n📈 {platform.upper()} 完成统计:")
        print(f"   上传成功: {success_count}")
        print(f"   上传失败: {fail_count}")
        total = len(self.video_files)
        if total > 0:
            print(f"   成功率: {(success_count / total * 100):.1f}%")


if __name__ == '__main__':
    scheduler = VideoSchedulerFinal()
    scheduler.run()
