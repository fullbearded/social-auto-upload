#!/usr/bin/env python3
"""
增强调度工具模块
支持开始日期配置、智能时间调整、发布计划确认等高级功能
"""

import random
import re
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from utils.log import logger

# 中文星期映射
CHINESE_WEEKDAYS = {
    'Monday': '星期一',
    'Tuesday': '星期二', 
    'Wednesday': '星期三',
    'Thursday': '星期四',
    'Friday': '星期五',
    'Saturday': '星期六',
    'Sunday': '星期日'
}

def parse_start_date(start_date_str: str) -> datetime:
    """
    解析开始日期字符串
    
    Args:
        start_date_str: 日期字符串，格式为 YYYY-MM-DD 或 'tomorrow'
    
    Returns:
        datetime: 解析后的日期对象
    """
    if not start_date_str or start_date_str.lower() == 'tomorrow':
        # 默认明天
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        # 尝试解析 YYYY-MM-DD 格式
        if re.match(r'^\d{4}-\d{2}-\d{2}$', start_date_str):
            parsed_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"日期格式错误: {start_date_str}")
    except ValueError as e:
        logger.error(f"日期解析失败: {e}")
        # 默认明天
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

def adjust_publish_times_for_today(publish_times: List[int], 
                                 current_time: datetime = None) -> List[int]:
    """
    如果开始日期是今天，智能调整发布时间
    
    Args:
        publish_times: 原始发布时间列表（小时）
        current_time: 当前时间，默认为现在
    
    Returns:
        List[int]: 调整后的发布时间列表
    """
    if current_time is None:
        current_time = datetime.now()
    
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # 过滤掉当前时间2小时前的时间点
    valid_times = []
    for hour in publish_times:
        # 如果发布时间在当前时间2小时后，保留
        if hour > current_hour + 2:
            valid_times.append(hour)
        elif hour == current_hour + 2 and current_minute <= 30:
            # 如果正好是2小时后，但分钟还没过30分，也保留
            valid_times.append(hour)
    
    # 如果没有合适的时间点，使用所有时间点中大于当前时间的
    if not valid_times:
        valid_times = [hour for hour in publish_times if hour > current_hour]
    
    # 如果还是没有，使用明天的第一个时间点
    if not valid_times and publish_times:
        logger.info(f"⚠️ 今天没有合适的发布时间，将使用明天的第一个时间点 {publish_times[0]}:00")
        return []
    
    return valid_times

def generate_smart_schedule(video_files: List, 
                          publish_times: List[int],
                          start_date_str: str = 'tomorrow',
                          group_size: int = 5,
                          random_minutes: int = 10) -> Tuple[List[datetime], Dict]:
    """
    生成智能调度计划，支持开始日期和时间调整
    
    Args:
        video_files: 视频文件列表
        publish_times: 每天发布时间列表（小时）
        start_date_str: 开始日期字符串
        group_size: 分组大小
        random_minutes: 随机分钟偏移
    
    Returns:
        Tuple: (发布时间列表, 计划详情)
    """
    # 解析开始日期
    start_date = parse_start_date(start_date_str)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 检查是否是今天
    is_today = start_date.date() == today.date()
    
    # 导入原始调度函数
    from utils.scheduler_utils import generate_advanced_schedule
    
    # 如果是今天，需要特殊处理：
    # 1. 今天使用调整后的时间
    # 2. 从第二天开始使用完整的时间列表
    if is_today:
        # 首先获取今天调整后的时间
        today_adjusted_times = adjust_publish_times_for_today(publish_times)
        
        if not today_adjusted_times:
            # 今天没有合适的时间，调整为明天
            start_date = start_date + timedelta(days=1)
            days_offset = (start_date - today).days
            adjusted_publish_times = publish_times
            logger.info(f"📅 调整开始日期为: {start_date.strftime('%Y-%m-%d')}")
            
            # 使用完整的发布时间列表
            schedule_times, schedule_info = generate_advanced_schedule(
                video_files=video_files,
                daily_times=publish_times,
                group_size=group_size,
                start_days=days_offset,
                timestamps=False,
                random_minutes=random_minutes
            )
        else:
            # 今天有合适的时间，需要手动处理今天和后续日期的调度
            
            # 计算今天可以发布的视频数量（今天每个时间点发布一个视频）
            today_slots = len(today_adjusted_times)
            total_videos = len(video_files)
            
            if total_videos <= today_slots:
                # 所有视频今天就能发布完
                schedule_times = []
                for i, video_file in enumerate(video_files):
                    hour = today_adjusted_times[i]
                    schedule_time = datetime.now().replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    ) + timedelta(minutes=random.randint(0, random_minutes))
                    schedule_times.append(schedule_time)
                
                # 构建计划信息
                schedule_info = {
                    'total_videos': total_videos,
                    'total_days': 1,
                    'daily_plan': [{
                        'day': 1,
                        'videos': [{'publish_time': today_adjusted_times[i], 'video_index': i} 
                                  for i in range(total_videos)]
                    }],
                    'remainder_videos': [],
                    'shuffled_order': video_files
                }
                adjusted_publish_times = today_adjusted_times
            else:
                # 今天发布一部分，剩余的从明天开始使用完整时间列表
                
                # 今天的视频发布计划
                today_schedule_times = []
                for i in range(today_slots):
                    hour = today_adjusted_times[i]
                    schedule_time = datetime.now().replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    ) + timedelta(minutes=random.randint(0, random_minutes))
                    today_schedule_times.append(schedule_time)
                
                # 剩余视频从明天开始使用完整时间列表
                remaining_videos = video_files[today_slots:]
                remaining_schedule_times, remaining_schedule_info = generate_advanced_schedule(
                    video_files=remaining_videos,
                    daily_times=publish_times,  # 使用完整时间列表
                    group_size=group_size,
                    start_days=1,  # 从明天开始
                    timestamps=False,
                    random_minutes=random_minutes
                )
                
                # 合并时间列表
                schedule_times = today_schedule_times + remaining_schedule_times
                
                # 合并计划信息
                schedule_info = {
                    'total_videos': total_videos,
                    'total_days': 1 + remaining_schedule_info['total_days'],
                    'daily_plan': [{
                        'day': 1,
                        'videos': [{'publish_time': today_adjusted_times[i], 'video_index': i} 
                                  for i in range(today_slots)]
                    }] + [
                        {'day': day_info['day'] + 1, 'videos': day_info['videos']} 
                        for day_info in remaining_schedule_info['daily_plan']
                    ],
                    'remainder_videos': remaining_schedule_info.get('remainder_videos', []),
                    'shuffled_order': video_files[:today_slots] + remaining_schedule_info.get('shuffled_order', [])
                }
                adjusted_publish_times = today_adjusted_times
    else:
        # 不是今天，直接使用完整时间列表
        days_offset = (start_date - today).days
        adjusted_publish_times = publish_times
        schedule_times, schedule_info = generate_advanced_schedule(
            video_files=video_files,
            daily_times=publish_times,
            group_size=group_size,
            start_days=days_offset,
            timestamps=False,
            random_minutes=random_minutes
        )
    
    # 添加额外的调度信息
    schedule_info['start_date'] = start_date.strftime('%Y-%m-%d')
    schedule_info['is_today'] = is_today
    schedule_info['original_publish_times'] = publish_times
    schedule_info['adjusted_publish_times'] = adjusted_publish_times
    schedule_info['time_adjustment_reason'] = []
    
    if is_today and adjusted_publish_times != publish_times:
        schedule_info['time_adjustment_reason'].append(
            f"今天发布时间已调整，移除了当前时间2小时前的时间点"
        )
    
    return schedule_times, schedule_info

def print_detailed_schedule(schedule_times: List[datetime], 
                          schedule_info: Dict,
                          video_files: List) -> bool:
    """
    打印详细的发布计划供用户确认
    
    Args:
        schedule_times: 发布时间列表
        schedule_info: 计划详情
        video_files: 视频文件列表
    
    Returns:
        bool: 用户是否确认
    """
    print("\n📋 详细发布计划")
    print("=" * 80)
    
    # 基本信息
    print(f"📅 开始日期: {schedule_info['start_date']}")
    print(f"📹 视频总数: {len(video_files)}")
    print(f"📊 发布天数: {schedule_info['total_days']}")
    print(f"⏰ 每日发布时间: {schedule_info['adjusted_publish_times']}")
    
    if schedule_info['original_publish_times'] != schedule_info['adjusted_publish_times']:
        print(f"🔄 时间调整原因: {'; '.join(schedule_info['time_adjustment_reason'])}")
    
    print(f"🎲 随机时间偏移: 0-{schedule_info.get('random_minutes', 10)}分钟")
    print(f"📦 分组大小: {schedule_info.get('group_size', 5)}")
    
    # 每日详细计划
    print(f"\n📅 每日发布计划:")
    print("-" * 80)
    
    # 按日期分组发布时间
    daily_schedules = {}
    for idx, schedule_time in enumerate(schedule_times):
        date_key = schedule_time.strftime('%Y-%m-%d')
        if date_key not in daily_schedules:
            daily_schedules[date_key] = []
        
        video_name = Path(schedule_info['shuffled_order'][idx]).name
        daily_schedules[date_key].append({
            'time': schedule_time.strftime('%H:%M'),
            'video': video_name,
            'index': idx + 1
        })
    
    # 按日期顺序打印
    sorted_dates = sorted(daily_schedules.keys())
    for date in sorted_dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        english_weekday = date_obj.strftime('%A')
        chinese_weekday = CHINESE_WEEKDAYS.get(english_weekday, english_weekday)
        print(f"\n📅 {date} ({chinese_weekday}):")
        
        day_schedule = daily_schedules[date]
        day_schedule.sort(key=lambda x: x['time'])
        
        for item in day_schedule:
            print(f"   ⏰ {item['time']} - [{item['index']}] {item['video']}")
    
    # 统计信息
    print(f"\n📈 发布统计:")
    print("-" * 40)
    print(f"   总视频数: {len(video_files)}")
    print(f"   总发布次数: {len(schedule_times)}")
    print(f"   平均每天: {len(schedule_times) / max(len(sorted_dates), 1):.1f} 个视频")
    
    remainder_videos = schedule_info.get('remainder_videos', [])
    remainder_count = len(remainder_videos) if isinstance(remainder_videos, list) else remainder_videos
    if remainder_count > 0:
        print(f"   余数视频: {remainder_count} 个")
    
    # 确认提示
    print("\n" + "=" * 80)
    print("⚠️  请确认以上发布计划是否正确？")
    print("   - 确认后将开始按计划发布")
    print("   - 可以随时按 Ctrl+C 取消")
    print("=" * 80)
    
    while True:
        try:
            confirm = input("\n确认发布计划？(y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是', '确认']:
                return True
            elif confirm in ['n', 'no', '否', '取消']:
                return False
            else:
                print("请输入 y/n 或 是/否")
        except KeyboardInterrupt:
            print("\n❌ 用户取消")
            return False

def validate_schedule_config(video_files: List, 
                           publish_times: List[int],
                           start_date_str: str) -> Tuple[bool, str]:
    """
    验证调度配置
    
    Args:
        video_files: 视频文件列表
        publish_times: 发布时间列表
        start_date_str: 开始日期字符串
    
    Returns:
        Tuple[bool, str]: (是否有效, 错误消息)
    """
    if not video_files:
        return False, "没有找到视频文件"
    
    if not publish_times:
        return False, "没有设置发布时间"
    
    # 验证发布时间格式
    for hour in publish_times:
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            return False, f"发布时间格式错误: {hour}，必须是0-23之间的整数"
    
    # 验证开始日期
    try:
        start_date = parse_start_date(start_date_str)
        if start_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return False, "开始日期不能是过去的日期"
    except Exception as e:
        return False, f"开始日期格式错误: {e}"
    
    # 检查发布时间数量是否足够
    required_slots = len(video_files)
    available_slots_per_day = len(publish_times)
    
    if start_date_str == 'tomorrow' or parse_start_date(start_date_str).date() == datetime.now().date():
        # 如果是今天，检查调整后的时间是否足够
        adjusted_times = adjust_publish_times_for_today(publish_times)
        if not adjusted_times:
            # 今天没有合适的时间，但验证不报错，让调度算法自动处理
            logger.info("⚠️ 今天没有合适的发布时间，将自动调整为明天")
            available_slots_per_day = len(publish_times)  # 使用完整时间列表计算
        else:
            available_slots_per_day = len(adjusted_times)
    
    return True, "配置验证通过"