#!/usr/bin/env python3
"""
调度管理器 - 处理视频调度和映射逻辑
Schedule Manager - Handles video scheduling and mapping logic
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from pathlib import Path


class ScheduleManager:
    """调度管理器类"""
    
    @staticmethod
    def create_video_mapping(shuffled_videos: List[Path], schedule_info: Dict) -> Dict:
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
    
    @staticmethod
    def create_simple_mapping(schedule_info: Dict, video_files: List[Path]) -> Dict:
        """
        创建简单的视频到全局索引的映射
        
        Args:
            schedule_info: 调度信息
            video_files: 视频文件列表
            
        Returns:
            Dict: 视频文件到全局索引的映射
        """
        video_mapping = {}
        shuffled_order = schedule_info.get('shuffled_order', video_files)
        
        for global_idx, video_file in enumerate(shuffled_order):
            # 每个视频文件与全局一一对应
            video_mapping[video_file] = {
                'video_index': global_idx,
                'safe_index': global_idx
            }
        
        return video_mapping
    
    @staticmethod
    def get_video_info_for_display(video_file: Path, schedule_info: Dict) -> Dict:
        """
        获取用于显示的调度信息
        
        Args:
            video_file: 视频文件
            schedule_info: 调度信息
            
        Returns:
            Dict: 显示信息
        """
        shuffled_videos = schedule_info.get('shuffled_order', [])
        
        try:
            global_idx = shuffled_videos.index(video_file)
            return {
                'global_index': global_idx,
                'safe_index': global_idx,
                'filename': video_file.name
            }
        except ValueError:
            return {
                'global_index': -1,
                'safe_index': -1,
                'filename': video_file.name
            }
    
    @classmethod
    def calculate_daily_statistics(cls, schedule_info: Dict, video_files: List[Path]) -> Dict:
        """
        计算每日统计信息
        
        Args:
            schedule_info: 调度信息
            video_files: 视频文件列表
            
        Returns:
            Dict: 每日统计信息
        """
        total_videos = len(video_files)
        daily_plan = schedule_info.get('daily_plan', [])
        
        return {
            'total_videos': total_videos,
            'total_days': len(daily_plan),
            'groups': schedule_info.get('groups', []),
            'remainder_videos': schedule_info.get('remainder_videos', []),
            'daily_breakdown': [
                {
                    'day': daily_info['day'],
                    'videos_count': len(daily_info['videos']),
                    'videos': daily_info['videos']
                }
                for daily_info in daily_plan
            ]
        }
    
    @classmethod
    def print_schedule_summary(cls, schedule_info: Dict, video_files: List[Path]):
        """
        打印调度摘要（替代来自 scheduler_utils 的函数）
        
        Args:
            schedule_info: 调度信息
            video_files: 视频文件列表
        """
        stats = cls.calculate_daily_statistics(schedule_info, video_files)
        
        # 纯粹的摘要信息 - 无需返回，直接打印
        print(f"总视频数: {stats['total_videos']}, 发布天数: {stats['total_days']}")
        
        if stats['remainder_videos']:
            print(f"余数视频: {len(stats['remainder_videos'])}个")
    
    @classmethod
    def generate_schedule_summary(cls, schedule_info: Dict, video_files: List[Path]) -> Dict:
        """
        兼容性的调度摘要生成
        
        Args:
            schedule_info: 调度信息
            video_files: 视频文件列表
            
        Returns:
            Dict: 调度摘要
        """
        stats = cls.calculate_daily_statistics(schedule_info, video_files)
        
        shuffled_order = schedule_info.get('shuffled_order', video_files)
        original_order = sorted(video_files, key=lambda x: x.name)
        
        return {
            'statistics': stats,
            'original_order': [f.name for f in original_order],
            'shuffled_order': [f.name for f in shuffled_order],
            'remainder_info': {
                'has_remainder': len(stats['remainder_videos']) > 0,
                'count': len(stats['remainder_videos']),
                'description': "余数视频放在最后一天的前几个时间点"
            }
        }