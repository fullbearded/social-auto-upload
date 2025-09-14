#!/usr/bin/env python3
"""
多平台智能视频调度发布器 - 增强版
支持开始日期配置、智能时间调整、发布缓存、失败重试等高级功能
"""

import asyncio, sys, os, random, re
from datetime import datetime

# Windows系统编码处理
if sys.platform == 'win32': os.system('chcp 65001')

from pathlib import Path
from utils.files_times import get_title_and_hashtags
from utils.tencent_risk_control import TencentRiskController
from utils.countdown import countdown_for_platform
from utils.publish_cache import PublishCache

# 增强调度工具
from utils.enhanced_scheduler import (
    generate_smart_schedule, 
    print_detailed_schedule, 
    validate_schedule_config,
    parse_start_date
)

# 工具类
from utils.scheduler.platform_manager import PlatformManager
from utils.scheduler.upload_engine import UploadEngine
from utils.scheduler.file_manager import FileManager
from utils.scheduler.ui_manager import UIManager
from utils.scheduler.config_manager import ConfigManager


class VideoSchedulerFinal:
    """增强版视频调度器"""

    def __init__(self):
        self.config = ConfigManager.create_scheduler_config()
        self.platforms = []
        self.video_files = []
        self.schedule = {}
        self.publish_datetimes = []
        self.start_date = None
        self.publish_cache = PublishCache()

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

            # 3. 获取开始日期
            self.start_date = self._get_start_date()

            # 4. 验证配置
            is_valid, message = validate_schedule_config(
                self.video_files, 
                self.config['publish_times'], 
                self.start_date
            )
            if not is_valid:
                print(f"❌ 配置验证失败: {message}")
                return

            # 5. 显示缓存状态
            self._show_cache_status()

            # 6. 创建智能调度计划
            if not self._create_smart_schedule():
                return

            # 7. 详细计划确认
            if not print_detailed_schedule(self.publish_datetimes, self.schedule, self.video_files):
                print("❌ 发布取消")
                return

            # 8. 执行发布
            self._execute_publishing()

            # 9. 最终统计
            UIManager.print_final_completion_stats(
                len(self.video_files),
                self.schedule,
                PlatformManager.get_all_platforms()
            )

        except KeyboardInterrupt:
            print("\n❌ 用户取消")
        except Exception as e:
            print(f"\n❌ 运行错误: {e}")
            import traceback
            traceback.print_exc()

    def _get_start_date(self):
        """获取开始日期"""
        print(f"\n📅 开始日期设置")
        print(f"   默认: 明天")
        
        while True:
            try:
                start_date_input = input("请输入开始日期 (YYYY-MM-DD，回车使用明天): ").strip()
                if not start_date_input:
                    return "tomorrow"
                
                # 验证日期格式
                if re.match(r'^\d{4}-\d{2}-\d{2}$', start_date_input):
                    # 验证日期是否有效
                    parsed_date = datetime.strptime(start_date_input, '%Y-%m-%d')
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if parsed_date < today:
                        print("   ❌ 开始日期不能是过去的日期，请重新输入")
                        continue
                    
                    print(f"   ✅ 使用开始日期: {start_date_input}")
                    return start_date_input
                else:
                    print("   ❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
            except ValueError:
                print("   ❌ 日期无效，请重新输入")
            except KeyboardInterrupt:
                print("   ⚠️ 使用默认开始日期: 明天")
                return "tomorrow"

    def _show_cache_status(self):
        """显示缓存状态"""
        print(f"\n📊 发布缓存状态")
        print("=" * 50)
        
        for platform in self.platforms:
            published_count = len(self.publish_cache.cache_data["published_videos"].get(platform, {}))
            failed_count = len(self.publish_cache.cache_data["failed_videos"].get(platform, {}))
            
            print(f"📱 {platform.upper()}:")
            print(f"   ✅ 已发布: {published_count} 个视频")
            print(f"   ❌ 发布失败: {failed_count} 个视频")
        
        print("=" * 50)
        
        # 询问是否清除缓存
        try:
            clear_cache = input("\n是否清除所有缓存？(y/n，默认n): ").strip().lower()
            if clear_cache in ['y', 'yes', '是']:
                self.publish_cache.clear_all_cache()
                print("✅ 已清除所有缓存")
        except KeyboardInterrupt:
            pass

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

    def _create_smart_schedule(self):
        """创建智能调度计划"""
        try:
            self.publish_datetimes, self.schedule = generate_smart_schedule(
                video_files=self.video_files,
                publish_times=self.config['publish_times'],
                start_date_str=self.start_date,
                group_size=self.config['group_size'],
                random_minutes=self.config['random_minutes']
            )

            # 显示计划摘要
            print(f"\n📊 智能调度计划已生成")
            print(f"   📅 开始日期: {self.schedule.get('start_date')}")
            print(f"   📹 视频总数: {len(self.video_files)}")
            print(f"   📊 发布天数: {self.schedule.get('total_days', 0)}")
            print(f"   ⏰ 原始发布时间: {self.schedule.get('original_publish_times', [])}")
            print(f"   ⏰ 调整后发布时间: {self.schedule.get('adjusted_publish_times', [])}")
            
            if self.schedule.get('time_adjustment_reason'):
                for reason in self.schedule['time_adjustment_reason']:
                    print(f"   📝 {reason}")

            remainder = len(self.schedule.get('remainder_videos', []))
            if remainder > 0:
                print(f"   📦 余数处理: {remainder}个视频")

            return True
        except Exception as e:
            print(f"❌ 调度计划生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _execute_publishing(self):
        """执行多平台发布"""
        UIManager.print_start_message()

        for platform in self.platforms:
            self._publish_single_platform(platform)

    def _publish_single_platform(self, platform):
        """发布到指定平台"""
        print(f"\n{'=' * 60}")
        print(f"📱 {platform.upper()} 平台发布")
        print(f"{'=' * 60}")

        # 检查缓存中的失败视频，优先重试
        failed_videos = self.publish_cache.get_platform_failed_videos(platform)
        if failed_videos:
            print(f"🔄 发现 {len(failed_videos)} 个失败视频，将优先重试")

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
            success, fail, skip = 0, 0, 0

            # 获取待发布视频列表（排除已发布的）
            videos_to_publish = []
            for idx, video in enumerate(self.schedule.get('shuffled_order', self.video_files)):
                if idx >= len(self.publish_datetimes):
                    break

                video_path = str(video)
                
                # 检查是否已发布
                if self.publish_cache.is_video_published(platform, video_path):
                    print(f"⏭️  [{idx + 1}/{len(self.video_files)}] {video.name} (已发布，跳过)")
                    skip += 1
                    continue
                
                videos_to_publish.append((idx, video, self.publish_datetimes[idx]))

            print(f"📋 需要发布 {len(videos_to_publish)} 个视频 (已跳过 {skip} 个已发布视频)")

            for idx, video, publish_time in videos_to_publish:
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
                    print(f"\n📹 [{idx + 1}/{len(self.video_files)}] 处理视频")
                    print(f"   文件名: {video.name}")
                    print(f"   标题: {title}")
                    print(f"   标签: {tags}")
                    print(f"   计划发布时间: {publish_time.strftime('%Y-%m-%d %H:%M')}")
                    if thumbnail_path:
                        print(f"   封面: {Path(thumbnail_path).name}")
                    else:
                        print(f"   封面: 无封面图（使用平台默认）")

                    result = await UploadEngine.upload_video_to_platform(
                        platform=platform,
                        video_file=video,
                        title=title,
                        tags=tags,
                        publish_time=publish_time,
                        video_info={'global_index': idx, 'thumbnail_path': thumbnail_path},
                        risk_controller=risk
                    )

                    if result:
                        success += 1
                        # 标记为已发布
                        self.publish_cache.mark_video_published(platform, str(video), publish_time)
                        print(f"✅ 发布成功: {video.name}")
                    else:
                        fail += 1
                        # 标记为发布失败
                        self.publish_cache.mark_video_failed(platform, str(video), publish_time, "上传失败")
                        print(f"❌ 发布失败: {video.name}")

                    if idx < len(videos_to_publish) - 1:
                        delay = random.randint(20, 60)
                        await countdown_for_platform(platform, delay)

                except Exception as e:
                    fail += 1
                    # 标记为发布失败
                    error_msg = str(e)[:500]  # 限制错误消息长度
                    self.publish_cache.mark_video_failed(platform, str(video), publish_time, error_msg)
                    print(f"❌ 处理失败: {video.name} - {error_msg}")

            return success, fail, skip

        success_count, fail_count, skip_count = asyncio.run(_upload_all_videos())

        # 平台统计
        print(f"\n📈 {platform.upper()} 发布完成统计:")
        print(f"   ✅ 上传成功: {success_count}")
        print(f"   ❌ 上传失败: {fail_count}")
        print(f"   ⏭️  已跳过: {skip_count}")
        total = len(self.video_files)
        if total > 0:
            print(f"   📊 成功率: {(success_count / (success_count + fail_count) * 100):.1f}% (不包括已跳过)")
        
        # 显示失败视频重试建议
        if fail_count > 0:
            failed_videos = self.publish_cache.get_platform_failed_videos(platform)
            if failed_videos:
                print(f"\n🔄 失败视频重试建议:")
                for fail_video in failed_videos[-3:]:  # 显示最近3个失败视频
                    retry_count = fail_video['retry_count']
                    print(f"   - {Path(fail_video['video_path']).name} (重试次数: {retry_count})")
                print(f"   💡 提示: 重新运行脚本将自动重试失败的视频")


if __name__ == '__main__':
    scheduler = VideoSchedulerFinal()
    scheduler.run()
