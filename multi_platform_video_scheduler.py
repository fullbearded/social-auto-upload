#!/usr/bin/env python3
"""
多平台智能视频调度发布器 (Multi-Platform Video Scheduler)
支持8个主流社交媒体平台的自动化视频发布

功能特点：
- 🔀 智能随机打乱视频顺序，避免固定模式
- 📊 动态分组算法（每5个视频为一组）
- ⏰ 智能时间调度：6/9/12/17/19点，支持0-10分钟随机偏移
- 🎯 余数智能处理（41个视频时自动调整）
- 📅 动态计算发布天数，自动生成完整计划
- 📈 详细的发布统计和可视化展示
- 🌐 8大平台同时发布支持
- 🎮 交互式平台选择界面
- 🛡️ 智能Cookie验证和错误处理

支持平台（8个）：
- 抖音 (douyin) - 支持自定义封面，需要创作者账号
- 哔哩哔哩 (bilibili) - 需要biliup库，支持分区选择
- 小红书 (xiaohongshu) - 支持自定义封面和地理位置
- 快手 (kuaishou) - 限制最多3个话题标签
- 百家号 (baijiahao) - 支持AI成片功能，需要创作者权限
- 腾讯视频号 (tencent) - 支持原创声明和商品添加
- TikTok (tk) - 使用Firefox浏览器，需要特殊网络环境
- 快手备用 (ks) - 功能类似主快手上传器

使用方法：
    python multi_platform_video_scheduler.py
    
详细说明请参考：MULTI_PLATFORM_VIDEO_SCHEDULER_USAGE.md
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from conf import BASE_DIR
from utils.files_times import get_title_and_hashtags
from utils.scheduler_utils import (
    generate_advanced_schedule, 
    print_schedule_summary, 
    validate_video_schedule,
    shuffle_and_group_videos
)

# 导入各平台的上传器和设置函数
from uploader.douyin_uploader.main import DouYinVideo, douyin_setup
from uploader.bilibili_uploader.main import BilibiliUploader, read_cookie_json_file, extract_keys_from_json
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo, xiaohongshu_setup
from uploader.kuaishou_uploader.main import KuaiShouVideo, kuaishou_setup
from uploader.baijiahao_uploader.main import BaiJiaHaoVideo, baijiahao_setup
from uploader.tencent_uploader.main import TencentVideo, weixin_setup
from uploader.tk_uploader.main import TiktokVideo, tiktok_setup
from uploader.ks_uploader.main import KSVideo, ks_setup
# 注意：xhs_uploader使用不同的架构，暂时不纳入调度系统


def get_platform_uploader(platform):
    """获取对应平台的上传器类"""
    uploaders = {
        'douyin': DouYinVideo,
        'bilibili': BilibiliUploader,
        'xiaohongshu': XiaoHongShuVideo,
        'kuaishou': KuaiShouVideo,
        'baijiahao': BaiJiaHaoVideo,
        'tencent': TencentVideo,
        'tk': TiktokVideo,
        'ks': KSVideo,
    }
    return uploaders.get(platform)


def get_cookie_path(platform):
    """获取对应平台的cookie文件路径"""
    cookie_paths = {
        'douyin': Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json",
        'bilibili': Path(BASE_DIR) / "cookies" / "bilibili_uploader" / "account.json",
        'xiaohongshu': Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json",
        'kuaishou': Path(BASE_DIR) / "cookies" / "kuaishou_uploader" / "account.json",
        'baijiahao': Path(BASE_DIR) / "cookies" / "baijiahao_uploader" / "account.json",
        'tencent': Path(BASE_DIR) / "cookies" / "tencent_uploader" / "account.json",
        'tk': Path(BASE_DIR) / "cookies" / "tk_uploader" / "account.json",
        'ks': Path(BASE_DIR) / "cookies" / "ks_uploader" / "account.json",
    }
    return cookie_paths.get(platform)


async def setup_platform_cookies(platform):
    """设置平台cookie"""
    cookie_path = get_cookie_path(platform)
    
    try:
        if platform == 'douyin':
            return await douyin_setup(cookie_path, handle=False)
        elif platform == 'bilibili':
            # Bilibili没有setup函数，检查cookie文件是否存在
            return cookie_path.exists()
        elif platform == 'xiaohongshu':
            return await xiaohongshu_setup(cookie_path, handle=False)
        elif platform == 'kuaishou':
            return await kuaishou_setup(cookie_path, handle=False)
        elif platform == 'baijiahao':
            return await baijiahao_setup(cookie_path, handle=False)
        elif platform == 'tencent':
            return await weixin_setup(cookie_path, handle=False)
        elif platform == 'tk':
            return await tiktok_setup(cookie_path, handle=False)
        elif platform == 'ks':
            return await ks_setup(cookie_path, handle=False)
        else:
            print(f"⚠️  平台 {platform} 未找到setup函数，跳过cookie验证")
            return True
    except Exception as e:
        print(f"❌ {platform} Cookie设置错误: {e}")
        return False


async def upload_video_to_platform(platform, video_file, title, tags, publish_time, video_info):
    """上传视频到指定平台"""
    uploader_class = get_platform_uploader(platform)
    cookie_path = get_cookie_path(platform)
    
    if not uploader_class:
        print(f"❌ 不支持的平台: {platform}")
        return False
    
    try:
        # 检查封面文件
        thumbnail_path = video_file.with_suffix('.png')
        
        # 打印上传信息
        time_str = publish_time.strftime('%Y-%m-%d %H:%M')
        remainder_flag = " (余数)" if video_info.get('is_remainder') else ""
        group_info = f" (第{video_info.get('group_id', 0)}组)" if video_info.get('group_id') else ""
        
        # 计算相对于基准时间的偏移
        base_hour = video_info.get('base_hour', int(time_str.split(' ')[1].split(':')[0]))
        actual_minute = int(time_str.split(' ')[1].split(':')[1])
        time_offset_info = f" (+{actual_minute}分钟)" if actual_minute > 0 else ""
        
        print(f"\n📤 上传视频: {video_file.name}")
        print(f"   标题: {title}")
        print(f"   标签: {tags}")
        print(f"   时间: {time_str}{time_offset_info}{remainder_flag}{group_info}")
        
        if thumbnail_path.exists():
            print(f"   封面: {thumbnail_path.name}")
            app = uploader_class(title, str(video_file), tags, publish_time, str(cookie_path), thumbnail_path=str(thumbnail_path))
        else:
            app = uploader_class(title, str(video_file), tags, publish_time, str(cookie_path))
        
        # 执行上传
        await app.main()
        return True
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return False


def create_video_mapping(shuffled_videos: List, schedule_info: Dict) -> Dict:
    """
    创建视频文件到调度信息的映射
    
    Args:
        shuffled_videos: 打乱后的视频列表
        schedule_info: 调度信息
        
    Returns:
        Dict: 视频文件到调度信息的映射
    """
    video_mapping = {}
    
    # 为每个视频分配组ID
    current_group = 0
    videos_in_group = 0
    
    for video_idx, video_file in enumerate(shuffled_videos):
        # 确定组ID
        if videos_in_group >= 5:  # 每组5个视频
            current_group += 1
            videos_in_group = 0
        
        video_mapping[video_file] = {
            'video_index': video_idx,
            'group_id': current_group + 1,
            'is_remainder': False
        }
        videos_in_group += 1
    
    # 更新余数视频信息
    for daily_info in schedule_info['daily_plan']:
        for video_info in daily_info['videos']:
            video_idx = video_info['video_index']
            if video_idx < len(shuffled_videos):
                video_file = shuffled_videos[video_idx]
                if video_file in video_mapping:
                    video_mapping[video_file]['is_remainder'] = video_info.get('is_remainder', False)
                    video_mapping[video_file]['publish_time'] = video_info['publish_time']
                    video_mapping[video_file]['day'] = daily_info['day']
    
    return video_mapping


def get_platform_notes():
    """获取各平台的特殊说明"""
    return {
        'douyin': '支持自定义封面，需要抖音创作者账号',
        'bilibili': '需要biliup库，支持视频分区选择',
        'xiaohongshu': '支持自定义封面和地理位置',
        'kuaishou': '限制最多3个话题标签',
        'baijiahao': '支持AI成片功能，需要百家号创作者权限',
        'tencent': '腾讯视频号，支持原创声明和商品添加',
        'tk': 'TikTok，使用Firefox浏览器（特殊）',
        'ks': '快手备用上传器，功能类似',
    }


def select_platforms():
    """选择要发布的平台"""
    available_platforms = {
        'douyin': '抖音',
        'bilibili': '哔哩哔哩',
        'xiaohongshu': '小红书',
        'kuaishou': '快手',
        'baijiahao': '百家号',
        'tencent': '腾讯视频号',
        'tk': 'TikTok',
        'ks': '快手(备用)',
    }
    
    print("\n📱 请选择要发布的平台（输入平台编号，多个平台用逗号分隔）:")
    platform_list = list(available_platforms.items())
    platform_notes = get_platform_notes()
    
    for i, (key, name) in enumerate(platform_list, 1):
        note = platform_notes.get(key, '')
        note_str = f" - {note}" if note else ""
        print(f"  {i}. {name} ({key}){note_str}")
    
    print("\n💡 示例输入: 1,2,3  (表示选择抖音、哔哩哔哩、小红书)")
    print("   直接按回车使用默认配置: 抖音 + 哔哩哔哩")
    
    try:
        user_input = input("\n请选择平台: ").strip()
        
        if not user_input:  # 默认配置
            return ['douyin', 'bilibili']
        
        # 解析用户输入
        selected_indices = []
        for part in user_input.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part)
                if 1 <= idx <= len(platform_list):
                    selected_indices.append(idx - 1)
        
        if selected_indices:
            selected_platforms = [platform_list[i][0] for i in selected_indices]
            print(f"✅ 已选择平台: {', '.join([f'{p}({available_platforms[p]})' for p in selected_platforms])}")
            return selected_platforms
        else:
            print("⚠️  输入无效，使用默认配置")
            return ['douyin', 'bilibili']
            
    except (KeyboardInterrupt, EOFError):
        print("\n❌ 用户取消选择")
        return ['douyin', 'bilibili']
    except Exception as e:
        print(f"❌ 选择平台时出错: {e}")
        return ['douyin', 'bilibili']


def main():
    """多平台智能视频调度发布器主函数"""
    print("🚀 === 多平台智能视频调度发布器 === 🚀")
    print("🌐 支持8大主流平台 | ⏰ 智能时间调度 | 🎲 随机偏移")
    print("📋 详细说明: MULTI_PLATFORM_VIDEO_SCHEDULER_USAGE.md")
    print("=" * 60)
    
    # 配置参数
    available_platforms = {
        'douyin': '抖音',
        'bilibili': '哔哩哔哩',
        'xiaohongshu': '小红书',
        'kuaishou': '快手',
        'baijiahao': '百家号',
        'tencent': '腾讯视频号',
        'tk': 'TikTok',
        'ks': '快手(备用)',
    }
    
    # 选择平台
    platforms = select_platforms()
    
    videos_dir = Path(BASE_DIR) / "videos"
    daily_publish_times = [6, 9, 12, 17, 19]  # 每天发布时间
    group_size = 5  # 每组视频数量
    start_days = 0  # 从明天开始
    
    print(f"\n📅 发布时间: {[f'{t}:00' for t in daily_publish_times]}")
    print(f"📊 每组视频: {group_size}个")
    print(f"🚀 发布平台: {', '.join([f'{p}({available_platforms[p]})' for p in platforms])}")
    
    # 获取视频文件
    if not videos_dir.exists():
        print(f"❌ 视频目录不存在: {videos_dir}")
        return
    
    video_files = list(videos_dir.glob("*.mp4"))
    if not video_files:
        print("❌ 没有找到视频文件")
        return
    
    # 验证计划可行性
    if not validate_video_schedule(video_files, daily_publish_times):
        return
    
    total_videos = len(video_files)
    print(f"📹 发现视频: {total_videos}个")
    
    # 生成高级调度计划
    print("\n🤖 正在生成智能调度计划...")
    publish_datetimes, schedule_info = generate_advanced_schedule(
        video_files=video_files,
        daily_times=daily_publish_times,
        group_size=group_size,
        start_days=start_days,
        timestamps=False,
        random_minutes=10  # 添加0-10分钟的随机时间偏移
    )
    
    # 创建视频映射
    video_mapping = create_video_mapping(schedule_info['shuffled_order'], schedule_info)
    
    # 打印详细计划
    print_schedule_summary(schedule_info, video_files)
    
    # 显示随机打乱结果
    print(f"\n=== 🎲 视频随机打乱结果 ===")
    print(f"原始顺序: {[f.name for f in sorted(video_files, key=lambda x: x.name)]}")
    print(f"打乱顺序: {[f.name for f in schedule_info['shuffled_order']]}")
    
    # 特殊处理说明
    if schedule_info['remainder_videos']:
        print(f"\n⚠️  特殊处理:")
        print(f"   余数视频: {len(schedule_info['remainder_videos'])}个")
        print(f"   处理方式: 放在最后一天的前几个时间点")
    
    # 确认发布
    print(f"\n📋 总结:")
    print(f"   总视频数: {total_videos}")
    print(f"   发布天数: {schedule_info['total_days']}")
    print(f"   完整组数: {len(schedule_info['groups'])}")
    print(f"   余数处理: {'是' if schedule_info['remainder_videos'] else '否'}")
    
    confirm = input(f"\n🤔 确认执行发布计划？ (y/N): ")
    if confirm.lower() != 'y':
        print("❌ 发布已取消")
        return
    
    # 开始发布
    print(f"\n🚀 === 开始智能发布 === 🚀")
    
    for platform in platforms:
        print(f"\n{'='*50}")
        print(f"📱 发布到 {platform.upper()} 平台")
        print(f"{'='*50}")
        
        # 设置平台cookie
        try:
            cookie_setup = asyncio.run(setup_platform_cookies(platform))
            if not cookie_setup:
                print(f"❌ {platform} Cookie设置失败，跳过该平台")
                continue
            print(f"✅ {platform} Cookie验证成功")
        except Exception as e:
            print(f"❌ {platform} Cookie设置错误: {e}")
            continue
        
        # 按天发布，便于跟踪进度
        success_count = 0
        fail_count = 0
        
        for daily_info in schedule_info['daily_plan']:
            day = daily_info['day']
            print(f"\n📅 第{day}天发布计划:")
            
            for video_info in daily_info['videos']:
                video_idx = video_info['video_index']
                
                if video_idx >= len(schedule_info['shuffled_order']):
                    continue
                
                video_file = schedule_info['shuffled_order'][video_idx]
                publish_time = publish_datetimes[video_idx]
                
                try:
                    # 获取标题和标签
                    title, tags = get_title_and_hashtags(str(video_file))
                    
                    # 获取视频信息
                    video_info_dict = video_mapping.get(video_file, {})
                    
                    # 上传到平台
                    success = asyncio.run(upload_video_to_platform(
                        platform=platform,
                        video_file=video_file,
                        title=title,
                        tags=tags,
                        publish_time=publish_time,
                        video_info=video_info_dict
                    ))
                    
                    if success:
                        success_count += 1
                        print(f"✅ 成功: {video_file.name}")
                    else:
                        fail_count += 1
                        print(f"❌ 失败: {video_file.name}")
                        
                except Exception as e:
                    fail_count += 1
                    print(f"❌ 处理视频 {video_file.name} 时出错: {e}")
                    continue
            
            # 每天发布完成后显示统计
            day_total = len(daily_info['videos'])
            day_success = success_count if daily_info == schedule_info['daily_plan'][-1] else "计算中..."
            print(f"\n📊 第{day}天统计: {day_total}个视频，成功:{day_success if isinstance(day_success, int) else '见最终统计'}")
        
        # 平台发布完成统计
        print(f"\n{'='*50}")
        print(f"📈 {platform.upper()} 平台发布完成统计:")
        print(f"   总视频数: {total_videos}")
        print(f"   成功: {success_count}")
        print(f"   失败: {fail_count}")
        print(f"   成功率: {(success_count/total_videos*100):.1f}%")
        print(f"{'='*50}")
    
    print(f"\n🎉 === 多平台智能发布完成 === 🎉")
    print(f"📊 最终统计报告:")
    print(f"   📹 总视频数: {total_videos}")
    print(f"   📅 发布天数: {schedule_info['total_days']}")
    print(f"   🎲 随机打乱: ✅")
    print(f"   📊 智能分组: ✅")
    print(f"   🎯 余数处理: ✅")
    print(f"   ⏰ 随机偏移: ✅")
    print(f"   🌐 支持平台: {len(available_platforms)}个")
    print(f"\n💡 使用说明详见: MULTI_PLATFORM_VIDEO_SCHEDULER_USAGE.md")
    print(f"🚀 多平台智能视频调度发布器 - 任务完成！")


if __name__ == '__main__':
    main()