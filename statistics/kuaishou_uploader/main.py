#!/usr/bin/env python3
"""
快手统计获取器 - 主接口
对应原uploader/ks_uploader/main.py结构
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from playwright.async_api import async_playwright

from utils.base_social_media import set_init_script
from utils.log import kuaishou_logger
from conf import BASE_DIR, LOCAL_CHROME_PATH

from .kuashou_scraper import KuaishouScraper
from .stats_models import KuaishouVideoStats, KuaishouAccountStats


class KuaishouStatsUploader:
    """快手数据统计上传器类
    
    主接口类，负责快手账号数据的获取和管理，
    设计结构与原KSVideo类保持一致，
    """
    
    def __init__(self, account_file: str = None):
        """初始化统计上传器
        
        Args:
            account_file: Cookie文件路径
        """
        self.account_file = str(account_file) if account_file else str(BASE_DIR / "cookies" / "ks_uploader" / "account.json")
        self.local_executable_path = LOCAL_CHROME_PATH
        self.scraper = KuaishouScraper(self.account_file, self.local_executable_path)
        
        kuaishou_logger.info(f"快手统计获取器已初始化，账号文件: {self.account_file}")
    
    async def collect_statistics(self) -> Dict[str, Any]:
        """获取快手账号统计信息
        
        Returns:
            Dict包含完整的统计信息
        """
        kuaishou_logger.info("开始快手数据收集...")
        
        try:
            # 使用scraper收集所有数据
            data = await self.scraper.collect_statistics()
            
            # 数据后处理和格式化
            processed_data = self._process_statistics(data)
            
            kuaishou_logger.info("快手数据收集完成")
            return processed_data
            
        except Exception as e:
            kuaishou_logger.error(f"数据统计失败: {e}")
            raise
    
    def _process_statistics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理和格式化统计数据"""
        try:
            # 验证数据完整性
            account_data = raw_data.get('account_summary', {})
            video_data = raw_data.get('video_details', [])
            
            # 创建标准化返回格式
            return {
                'platform': 'kuaishou',
                'account_info': {
                    'account_name': account_data.get('account_name', '未知'),
                    'account_id': account_data.get('account_id', 'unknown'),
                    'last_updated': datetime.now().isoformat()
                },
                'summary': {
                    'total_videos': account_data.get('total_videos', 0),
                    'total_views': account_data.get('total_views', 0),
                    'total_likes': account_data.get('total_likes', 0),
                    'total_comments': account_data.get('total_comments', 0),
                    'total_shares': account_data.get('total_shares', 0),
                    'followers': account_data.get('followers', 0)
                },
                'videos': self._format_video_stats(video_data),
                'metadata': {
                    'collection_date': raw_data.get('collection_time'),
                    'processing_time': raw_data.get('processing_time', 0),
                    'accuracy_status': 'complete' if len(video_data) > 0 else 'partial',
                    'data_source': '快手创作者平台',
                    'platform_url': 'https://cp.kuaishou.com/statistics/works'
                }
            }
            
        except Exception as e:
            kuaishou_logger.error(f"数据统计处理失败: {e}")
            raise
    
    def _format_video_stats(self, video_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化视频统计数据"""
        formatted_videos = []
        
        for video in video_data:
            if not video or not isinstance(video, dict):
                continue
                
            formatted_video = {
                'video_id': video.get('video_id', ''),
                'title': video.get('title', ''),
                'upload_time': video.get('upload_time', ''),
                'views': video.get('views', 0),
                'likes': video.get('likes', 0),
                'comments': video.get('comments', 0),
                'shares': video.get('shares', 0),
                'collections': video.get('collections', 0),
                'interaction_rate': video.get('like_rate', 0.0)
            }
            formatted_videos.append(formatted_video)
        
        return formatted_videos
    
    async def get_account_summary(self) -> KuaishouAccountStats:
        """获取账号概览数据"""
        try:
            account_summary = await self.scraper.get_account_summary()
            return KuaishouAccountStats.from_dict(account_summary)
        except Exception as e:
            kuaishou_logger.error(f"获取账号概览失败: {e}")
            raise
    
    async def get_recent_videos(self, limit: int = 50) -> List[KuaishouVideoStats]:
        """获取最近的视频统计"""
        try:
            video_data = await self.scraper.get_video_detail_stats()
            
            video_stats = []
            for video in video_data[:limit]:
                if video:
                    video_stats.append(KuaishouVideoStats.from_dict(video))
            
            return video_stats
        except Exception as e:
            kuaishou_logger.error(f"获取视频统计失败: {e}")
            raise
    
    async def validate_api_access(self) -> bool:
        """验证API访问权限
        
        Returns:
            bool: 是否验证成功
        """
        try:
            return await self.scraper.validate_cookie()
        except Exception as e:
            kuaishou_logger.error(f"API验证失败: {e}")
            return False
    
    def close(self):
        """关闭统计获取器"""
        if hasattr(self.scraper, 'close'):
            self.scraper.close()
        kuaishou_logger.info("快手统计获取器已关闭")


# 快捷访问函数
def get_kuaishou_statistics(account_file: str) -> Dict[str, Any]:
    """快速获取快手统计数据的函数
    
    Args:
        account_file: Cookie文件路径
        
    Returns:
        统计数据字典
    """
    
    async def _get_stats():
        uploader = KuaishouStatsUploader(account_file)
        return await uploader.collect_statistics()
    
    return asyncio.run(_get_stats())


# 导出接口
__all__ = ['KuaishouStatsUploader', 'get_kuaishou_statistics']