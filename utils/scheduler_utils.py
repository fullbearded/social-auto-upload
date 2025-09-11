"""
高级视频调度工具模块
支持随机分组、智能时间分配、余数处理等复杂场景
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import math


def shuffle_and_group_videos(video_files: List, group_size: int = 5) -> Tuple[List[List], List]:
    """
    随机打乱视频文件并按指定大小分组，返回分组列表和剩余视频
    
    Args:
        video_files: 视频文件列表
        group_size: 每组视频数量
        
    Returns:
        Tuple: (分组列表, 剩余视频列表)
    """
    # 创建副本并随机打乱
    shuffled_videos = video_files.copy()
    random.shuffle(shuffled_videos)
    
    # 计算完整组数和余数
    total_videos = len(shuffled_videos)
    full_groups = total_videos // group_size
    remainder = total_videos % group_size
    
    # 创建完整组
    groups = []
    for i in range(full_groups):
        start_idx = i * group_size
        end_idx = start_idx + group_size
        groups.append(shuffled_videos[start_idx:end_idx])
    
    # 处理剩余视频
    remainder_videos = []
    if remainder > 0:
        start_idx = full_groups * group_size
        remainder_videos = shuffled_videos[start_idx:]
    
    return groups, remainder_videos


def calculate_optimal_schedule(total_videos: int, daily_times: List[int], group_size: int = 5) -> Dict:
    """
    计算最优的发布计划，包括分组、天数分配、余数处理
    
    Args:
        total_videos: 总视频数量
        daily_times: 每天发布时间列表
        group_size: 每组视频数量
        
    Returns:
        Dict: 包含完整计划信息
    """
    # 基本参数
    videos_per_day = len(daily_times)
    
    # 计算完整天数和余数
    full_days = total_videos // videos_per_day
    remainder_videos = total_videos % videos_per_day
    
    # 计算需要的总天数（考虑余数可能需要额外一天）
    total_days = full_days + (1 if remainder_videos > 0 else 0)
    
    # 生成详细的每日计划
    daily_plan = []
    
    # 处理完整天数
    for day in range(full_days):
        day_videos = []
        for time_idx in range(videos_per_day):
            video_index = day * videos_per_day + time_idx
            if video_index < total_videos:
                day_videos.append({
                    'video_index': video_index,
                    'publish_time': daily_times[time_idx],
                    'is_remainder': False
                })
        daily_plan.append({
            'day': day + 1,
            'videos': day_videos,
            'type': 'full'
        })
    
    # 处理余数视频（放在最后一天）
    if remainder_videos > 0:
        remainder_day_videos = []
        for time_idx in range(remainder_videos):
            video_index = full_days * videos_per_day + time_idx
            remainder_day_videos.append({
                'video_index': video_index,
                'publish_time': daily_times[time_idx],
                'is_remainder': True
            })
        
        # 如果已经有完整天数，合并到现有最后一天
        if daily_plan:
            daily_plan[-1]['videos'].extend(remainder_day_videos)
            daily_plan[-1]['type'] = 'full_with_remainder'
        else:
            # 只有余数视频的情况
            daily_plan.append({
                'day': 1,
                'videos': remainder_day_videos,
                'type': 'remainder_only'
            })
    
    return {
        'total_videos': total_videos,
        'total_days': total_days,
        'videos_per_day': videos_per_day,
        'group_size': group_size,
        'full_days': full_days,
        'remainder_videos': remainder_videos,
        'daily_plan': daily_plan,
        'daily_times': daily_times
    }


def generate_advanced_schedule(video_files: List, daily_times: List[int], 
                             group_size: int = 5, start_days: int = 0, 
                             timestamps: bool = False, random_minutes: int = 10) -> Tuple[List[datetime], Dict]:
    """
    生成高级调度计划，支持随机分组和智能时间分配
    
    Args:
        video_files: 视频文件列表
        daily_times: 每天发布时间列表
        group_size: 每组视频数量
        start_days: 开始天数偏移
        timestamps: 是否返回时间戳
        random_minutes: 随机时间偏移范围（0-random_minutes分钟）
        
    Returns:
        Tuple: (发布时间列表, 计划详情)
    """
    # 随机打乱并分组
    groups, remainder_videos = shuffle_and_group_videos(video_files, group_size)
    
    # 计算总视频数
    total_videos = len(video_files)
    
    # 计算最优计划
    schedule_info = calculate_optimal_schedule(total_videos, daily_times, group_size)
    
    # 生成具体的发布时间
    schedule_times = []
    current_time = datetime.now()
    
    for daily_info in schedule_info['daily_plan']:
        day_offset = daily_info['day'] - 1 + start_days
        
        for video_info in daily_info['videos']:
            hour = video_info['publish_time']
            # 添加随机分钟偏移（0-random_minutes分钟）
            random_minute_offset = random.randint(0, random_minutes)
            time_offset = timedelta(
                days=day_offset + 1,  # +1 to start from next day
                hours=hour - current_time.hour,
                minutes=-current_time.minute + random_minute_offset,
                seconds=-current_time.second,
                microseconds=-current_time.microsecond
            )
            timestamp = current_time + time_offset
            schedule_times.append(timestamp)
    
    if timestamps:
        schedule_times = [int(time.timestamp()) for time in schedule_times]
    
    # 添加分组信息到计划详情
    schedule_info['groups'] = groups
    schedule_info['remainder_videos'] = remainder_videos
    schedule_info['shuffled_order'] = [item for group in groups for item in group] + remainder_videos
    
    return schedule_times, schedule_info


def print_schedule_summary(schedule_info: Dict, video_files: List):
    """
    打印调度计划摘要
    
    Args:
        schedule_info: 计划详情
        video_files: 原始视频文件列表
    """
    print("=== 📊 智能调度计划摘要 ===")
    print(f"总视频数: {schedule_info['total_videos']}")
    print(f"总天数: {schedule_info['total_days']}")
    print(f"每天发布次数: {schedule_info['videos_per_day']}")
    print(f"发布时间: {schedule_info['daily_times']}")
    print(f"随机时间偏移: 0-10分钟")
    print(f"完整天数: {schedule_info['full_days']}")
    print(f"余数视频: {schedule_info['remainder_videos']}")
    
    print("\n=== 📅 每日详细计划 ===")
    for daily_info in schedule_info['daily_plan']:
        day_type = "完整发布" if daily_info['type'] == 'full' else "余数处理"
        print(f"\n第{daily_info['day']}天 ({day_type}):")
        
        for video_info in daily_info['videos']:
            video_idx = video_info['video_index']
            time_str = f"{video_info['publish_time']:02d}:00"
            remainder_flag = " (余数)" if video_info.get('is_remainder') else ""
            
            if video_idx < len(schedule_info.get('shuffled_order', [])):
                video_name = schedule_info['shuffled_order'][video_idx].name
                print(f"  {time_str} - {video_name}{remainder_flag}")
            else:
                print(f"  {time_str} - 视频{video_idx + 1}{remainder_flag}")
    
    # 显示随机分组信息
    if 'groups' in schedule_info and schedule_info['groups']:
        print(f"\n=== 🎲 随机分组结果 ===")
        for i, group in enumerate(schedule_info['groups']):
            print(f"第{i+1}组 ({len(group)}个视频):")
            for video in group:
                print(f"  - {video.name}")
        
        if schedule_info['remainder_videos']:
            print(f"\n余数视频 ({len(schedule_info['remainder_videos'])}个):")
            for video in schedule_info['remainder_videos']:
                print(f"  - {video.name}")


def validate_video_schedule(video_files: List, daily_times: List[int]) -> bool:
    """
    验证视频调度计划的可行性
    
    Args:
        video_files: 视频文件列表
        daily_times: 每天发布时间列表
        
    Returns:
        bool: 是否可行
    """
    if not video_files:
        print("❌ 没有视频文件")
        return False
    
    if not daily_times:
        print("❌ 没有设置发布时间")
        return False
    
    total_videos = len(video_files)
    max_daily_videos = len(daily_times)
    
    if total_videos > 0 and max_daily_videos == 0:
        print("❌ 视频数量大于0但没有设置发布时间")
        return False
    
    # 计算所需天数
    required_days = math.ceil(total_videos / max_daily_videos)
    max_reasonable_days = 90  # 最多90天
    
    if required_days > max_reasonable_days:
        print(f"⚠️  警告: 需要 {required_days} 天，可能时间过长")
    
    print(f"✅ 计划验证通过: {total_videos}个视频，{max_daily_videos}次/天，约需{required_days}天")
    return True