#!/usr/bin/env python3
"""
多平台智能视频调度发布器 - 增强版
支持开始日期配置、智能时间调整、发布缓存、失败重试等高级功能
"""

import asyncio, sys, os, random, re, argparse
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


def parse_publish_times(time_str: str) -> list:
    """解析发布时间字符串，支持多种格式"""
    times = []
    
    # 移除空格和方括号
    time_str = time_str.strip().replace('[', '').replace(']', '')
    
    # 支持多种分隔符
    for part in time_str.replace(',', ' ').replace('，', ' ').split():
        try:
            # 处理像 "5,8,12,17,19" 或 "5 8 12 17 19" 这样的格式
            if ':' in part:
                # 处理 "HH:MM" 格式
                hour = int(part.split(':')[0])
                times.append(hour)
            else:
                # 处理纯数字格式
                hour = int(part)
                if 0 <= hour <= 23:
                    times.append(hour)
                else:
                    print(f"⚠️  无效时间: {hour}，请输入0-23之间的小时数")
        except ValueError:
            print(f"⚠️  无法解析时间: {part}")
    
    return times if times else None


class VideoSchedulerFinal:
    """增强版视频调度器"""

    def __init__(self, custom_times=None, custom_config=None):
        # 基础配置
        base_config = ConfigManager.create_scheduler_config()
        
        # 应用自定义发布时间
        if custom_times:
            base_config['publish_times'] = custom_times
        
        # 应用其他自定义配置
        if custom_config:
            base_config.update(custom_config)
        
        self.config = base_config
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

            # 3. 交互式设置配置参数
            self._interactive_config_setup()

            # 4. 获取开始日期
            self.start_date = self._get_start_date()

            # 5. 验证配置
            is_valid, message = validate_schedule_config(
                self.video_files, 
                self.config['publish_times'], 
                self.start_date
            )
            if not is_valid:
                print(f"❌ 配置验证失败: {message}")
                return

            # 6. 显示缓存状态
            self._show_cache_status()

            # 7. 创建智能调度计划
            if not self._create_smart_schedule():
                return

            # 8. 详细计划确认
            if not print_detailed_schedule(self.publish_datetimes, self.schedule, self.video_files):
                print("❌ 发布取消")
                return

            # 9. 执行发布
            self._execute_publishing()

            # 10. 最终统计
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

    def _interactive_config_setup(self):
        """交互式设置配置参数"""
        print(f"\n⚙️  配置参数设置")
        print("=" * 50)
        
        # 显示当前配置
        print(f"📋 当前配置:")
        print(f"   📅 发布时间: {self.config['publish_times']}")
        print(f"   🎲 分组大小: {self.config['group_size']}")
        print(f"   ⏱️  随机偏移: {self.config['random_minutes']}分钟")
        print(f"   📅 开始天数偏移: {self.config['start_days']}")
        
        # 询问是否修改配置
        try:
            modify_config = input(f"\n是否修改配置参数？(y/n，默认n): ").strip().lower()
            if modify_config in ['y', 'yes', '是']:
                self._modify_publish_times()
                self._modify_group_size()
                self._modify_random_minutes()
                self._modify_start_days()
                
                print(f"\n✅ 配置更新完成:")
                print(f"   📅 发布时间: {self.config['publish_times']}")
                print(f"   🎲 分组大小: {self.config['group_size']}")
                print(f"   ⏱️  随机偏移: {self.config['random_minutes']}分钟")
                print(f"   📅 开始天数偏移: {self.config['start_days']}")
            else:
                print(f"ℹ️  使用当前配置")
        except KeyboardInterrupt:
            print(f"\n⚠️  使用当前配置")

    def _modify_publish_times(self):
        """修改发布时间"""
        while True:
            try:
                print(f"\n📅 发布时间设置")
                print(f"   当前: {self.config['publish_times']}")
                print(f"   支持格式:")
                print(f"     - 单一时间: [9]")
                print(f"     - 多个时间: 9,15,20")
                print(f"     - 空格分隔: 9 15 20")
                
                times_input = input(f"请输入发布时间 (回车保持当前): ").strip()
                
                if not times_input:
                    print(f"   ℹ️  保持当前发布时间")
                    break
                
                # 解析时间
                parsed_times = parse_publish_times(times_input)
                if parsed_times:
                    self.config['publish_times'] = parsed_times
                    print(f"   ✅ 发布时间已更新: {parsed_times}")
                    break
                else:
                    print(f"   ❌ 格式错误，请重新输入")
            except KeyboardInterrupt:
                print(f"\n   ⚠️  保持当前发布时间")
                break

    def _modify_group_size(self):
        """修改分组大小"""
        while True:
            try:
                print(f"\n🎲 分组大小设置")
                print(f"   当前: {self.config['group_size']}")
                
                group_input = input(f"请输入分组大小 (回车保持当前): ").strip()
                
                if not group_input:
                    print(f"   ℹ️  保持当前分组大小")
                    break
                
                try:
                    group_size = int(group_input)
                    if group_size > 0:
                        self.config['group_size'] = group_size
                        print(f"   ✅ 分组大小已更新: {group_size}")
                        break
                    else:
                        print(f"   ❌ 分组大小必须大于0")
                except ValueError:
                    print(f"   ❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print(f"\n   ⚠️  保持当前分组大小")
                break

    def _modify_random_minutes(self):
        """修改随机时间偏移"""
        while True:
            try:
                print(f"\n⏱️  随机时间偏移设置")
                print(f"   当前: {self.config['random_minutes']}分钟")
                
                random_input = input(f"请输入随机偏移分钟数 (回车保持当前): ").strip()
                
                if not random_input:
                    print(f"   ℹ️  保持当前随机偏移")
                    break
                
                try:
                    random_minutes = int(random_input)
                    if random_minutes >= 0:
                        self.config['random_minutes'] = random_minutes
                        print(f"   ✅ 随机偏移已更新: {random_minutes}分钟")
                        break
                    else:
                        print(f"   ❌ 随机偏移必须大于等于0")
                except ValueError:
                    print(f"   ❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print(f"\n   ⚠️  保持当前随机偏移")
                break

    def _modify_start_days(self):
        """修改开始天数偏移"""
        while True:
            try:
                print(f"\n📅 开始天数偏移设置")
                print(f"   当前: {self.config['start_days']}")
                
                start_days_input = input(f"请输入开始天数偏移 (回车保持当前): ").strip()
                
                if not start_days_input:
                    print(f"   ℹ️  保持当前开始天数偏移")
                    break
                
                try:
                    start_days = int(start_days_input)
                    if start_days >= 0:
                        self.config['start_days'] = start_days
                        print(f"   ✅ 开始天数偏移已更新: {start_days}")
                        break
                    else:
                        print(f"   ❌ 开始天数偏移必须大于等于0")
                except ValueError:
                    print(f"   ❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print(f"\n   ⚠️  保持当前开始天数偏移")
                break

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


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='多平台智能视频调度发布器 - 增强版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python multi_platform_video_scheduler_final.py
  python multi_platform_video_scheduler_final.py --times '[9]'
  python multi_platform_video_scheduler_final.py --times '9,15,20'
  python multi_platform_video_scheduler_final.py --times '5,8,12,17,19' --start-date 2025-10-01
  python multi_platform_video_scheduler_final.py --group-size 3 --random-minutes 5
        """
    )
    
    # 发布时间设置
    parser.add_argument(
        '--times', '-t', 
        help=f'设置发布时间，如: "[9]" 或 "9,15,20" (默认: {ConfigManager.DEFAULT_PUBLISH_TIMES})'
    )
    
    # 开始日期设置
    parser.add_argument(
        '--start-date', '-d',
        help='设置开始日期，格式: YYYY-MM-DD (默认: 明天)'
    )
    
    # 分组大小设置
    parser.add_argument(
        '--group-size', '-gs', 
        type=int,
        help=f'设置分组大小 (默认: {ConfigManager.DEFAULT_GROUP_SIZE})'
    )
    
    # 随机时间偏移设置
    parser.add_argument(
        '--random-minutes', '-rm', 
        type=int,
        help=f'设置随机时间偏移分钟数 (默认: {ConfigManager.DEFAULT_RANDOM_MINUTES})'
    )
    
    # 其他配置
    parser.add_argument(
        '--start-days', '-sd',
        type=int,
        help='设置开始天数偏移 (默认: 0)'
    )
    
    # 显示版本信息
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 解析发布时间
    custom_times = None
    if args.times:
        custom_times = parse_publish_times(args.times)
        if custom_times is None:
            print(f"❌ 无法解析发布时间: {args.times}")
            print(f"💡 支持格式: '[9]', '9,15,20', '5 8 12 17 19'")
            return
        print(f"✅ 命令行设置发布时间: {custom_times}")
    
    # 构建自定义配置
    custom_config = {}
    
    if args.start_date:
        # 验证日期格式
        try:
            parsed_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            custom_config['start_date'] = args.start_date
            print(f"📅 命令行设置开始日期: {args.start_date}")
        except ValueError:
            print(f"❌ 日期格式错误: {args.start_date}，请使用 YYYY-MM-DD 格式")
            return
    
    if args.group_size is not None:
        if args.group_size > 0:
            custom_config['group_size'] = args.group_size
            print(f"🎲 命令行设置分组大小: {args.group_size}")
        else:
            print(f"❌ 分组大小必须大于0")
            return
    
    if args.random_minutes is not None:
        if args.random_minutes >= 0:
            custom_config['random_minutes'] = args.random_minutes
            print(f"⏱️  命令行设置随机偏移: {args.random_minutes}分钟")
        else:
            print(f"❌ 随机偏移必须大于等于0")
            return
    
    if args.start_days is not None:
        if args.start_days >= 0:
            custom_config['start_days'] = args.start_days
            print(f"📅 命令行设置开始天数偏移: {args.start_days}")
        else:
            print(f"❌ 开始天数必须大于等于0")
            return
    
    # 显示配置摘要
    print("\n" + "="*60)
    print("🚀 多平台智能视频调度发布器")
    print("="*60)
    
    # 创建调度器实例
    try:
        scheduler = VideoSchedulerFinal(custom_times=custom_times, custom_config=custom_config)
        scheduler.run()
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
