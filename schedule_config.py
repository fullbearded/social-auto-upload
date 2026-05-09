#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频发布计划配置工具
用于修改发布时间、查看计划、生成调度方案等
"""

import json
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scheduler_utils import generate_advanced_schedule, print_schedule_summary, validate_video_schedule


class ScheduleConfig:
    """发布计划配置类"""
    
    def __init__(self, config_file: str = "schedule_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "start_date": "2025-09-15",
            "total_videos": 3,
            "publish_days": 1,
            "daily_times": [5, 8, 12, 17, 19],
            "group_size": 5,
            "random_minutes": 10,
            "start_days_offset": 0
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有字段都存在
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"⚠️  加载配置文件失败: {e}，使用默认配置")
                return default_config
        else:
            # 创建默认配置文件
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ 配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                print(f"✅ 已更新 {key}: {value}")
            else:
                print(f"⚠️  未知配置项: {key}")
    
    def show_config(self):
        """显示当前配置"""
        print("=== 📋 当前发布计划配置 ===")
        print(f"📅 开始日期: {self.config['start_date']}")
        print(f"📹 视频总数: {self.config['total_videos']}")
        print(f"📊 发布天数: {self.config['publish_days']}")
        print(f"⏰ 发布时间: {self.config['daily_times']}")
        print(f"🎲 分组大小: {self.config['group_size']}")
        print(f"⏱️  随机时间偏移: 0-{self.config['random_minutes']}分钟")
        print(f"📅 开始天数偏移: {self.config['start_days_offset']}")


def parse_time_string(time_str: str) -> List[int]:
    """解析时间字符串，支持多种格式"""
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
    
    return times


def generate_schedule_from_config(config: ScheduleConfig):
    """根据配置生成发布计划"""
    # 创建模拟视频文件对象
    class VideoFile:
        def __init__(self, name):
            self.name = name
    
    # 模拟视频文件列表
    video_files = [VideoFile(f"视频_{i+1}.mp4") for i in range(config.config['total_videos'])]
    
    # 生成发布计划
    schedule_times, schedule_info = generate_advanced_schedule(
        video_files=video_files,
        daily_times=config.config['daily_times'],
        group_size=config.config['group_size'],
        start_days=config.config['start_days_offset'],
        random_minutes=config.config['random_minutes']
    )
    
    # 打印计划摘要
    print_schedule_summary(schedule_info, video_files)
    
    # 打印具体的发布时间
    print("\n=== 🕐 具体发布时间 ===")
    for i, time in enumerate(schedule_times):
        print(f"{i+1}. {time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(description='视频发布计划配置工具')
    parser.add_argument('--config', '-c', default='schedule_config.json', 
                       help='配置文件路径 (默认: schedule_config.json)')
    
    # 命令选项
    parser.add_argument('--show', '-s', action='store_true', help='显示当前配置')
    parser.add_argument('--generate', '-g', action='store_true', help='生成发布计划')
    parser.add_argument('--update', '-u', nargs='+', help='更新配置，格式: key=value')
    
    # 具体配置项
    parser.add_argument('--start-date', '-d', help='设置开始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--total-videos', '-v', type=int, help='设置视频总数')
    parser.add_argument('--publish-days', '-p', type=int, help='设置发布天数')
    parser.add_argument('--times', '-t', help='设置发布时间，如: "5,8,12,17,19" 或 "[9]"')
    parser.add_argument('--group-size', '-gs', type=int, help='设置分组大小')
    parser.add_argument('--random-minutes', '-rm', type=int, help='设置随机时间偏移分钟数')
    parser.add_argument('--start-offset', '-so', type=int, help='设置开始天数偏移')
    
    args = parser.parse_args()
    
    # 初始化配置
    config = ScheduleConfig(args.config)
    
    # 处理各种命令
    if args.show and not any([args.start_date, args.total_videos is not None, args.publish_days is not None, 
                             args.times, args.group_size is not None, args.random_minutes is not None, 
                             args.start_offset is not None, args.update]):
        config.show_config()
        return
    
    if args.generate and not any([args.start_date, args.total_videos is not None, args.publish_days is not None, 
                                 args.times, args.group_size is not None, args.random_minutes is not None, 
                                 args.start_offset is not None, args.update]):
        generate_schedule_from_config(config)
        return
    
    # 更新配置
    updates = {}
    
    if args.start_date:
        # 验证日期格式
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
            updates['start_date'] = args.start_date
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
            return
    
    if args.total_videos is not None:
        updates['total_videos'] = args.total_videos
    
    if args.publish_days is not None:
        updates['publish_days'] = args.publish_days
    
    if args.times:
        times = parse_time_string(args.times)
        if times:
            updates['daily_times'] = times
            print(f"✅ 已设置发布时间: {times}")
        else:
            print("❌ 无法解析时间格式")
            return
    
    if args.group_size is not None:
        updates['group_size'] = args.group_size
    
    if args.random_minutes is not None:
        updates['random_minutes'] = args.random_minutes
    
    if args.start_offset is not None:
        updates['start_days_offset'] = args.start_offset
    
    # 处理 key=value 格式的更新
    if args.update:
        for item in args.update:
            if '=' in item:
                key, value = item.split('=', 1)
                try:
                    # 尝试解析为 JSON 值
                    parsed_value = json.loads(value)
                    updates[key] = parsed_value
                except json.JSONDecodeError:
                    # 如果不是 JSON，直接作为字符串
                    updates[key] = value
            else:
                print(f"⚠️  忽略无效的配置项: {item}")
    
    # 应用更新
    if updates:
        config.update_config(**updates)
        config.save_config()
        config.show_config()
    else:
        # 没有指定任何操作，显示帮助
        print("视频发布计划配置工具")
        print("使用 --help 查看帮助")
        print("\n常用命令:")
        print("  python schedule_config.py --show                    # 显示当前配置")
        print("  python schedule_config.py --generate                # 生成发布计划")
        print("  python schedule_config.py --times '[9]'              # 设置发布时间为9点")
        print("  python schedule_config.py --times '5,8,12,17,19'     # 设置多个发布时间")
        print("  python schedule_config.py --total-videos 10          # 设置视频总数为10")
        print("  python schedule_config.py --start-date 2025-10-01   # 设置开始日期")


if __name__ == "__main__":
    main()