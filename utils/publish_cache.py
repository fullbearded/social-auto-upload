#!/usr/bin/env python3
"""
发布缓存管理系统
管理已发布视频的缓存，避免重复发布
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from utils.log import logger

class PublishCache:
    """发布缓存管理器"""
    
    def __init__(self, cache_file: str = "publish_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """加载缓存数据"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存文件失败: {e}")
        
        return {
            "published_videos": {},  # {platform: {video_path: publish_info}}
            "failed_videos": {},     # {platform: {video_path: fail_info}}
            "last_update": None
        }
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            self.cache_data["last_update"] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存文件失败: {e}")
    
    def is_video_published(self, platform: str, video_path: str) -> bool:
        """检查视频是否已发布"""
        return platform in self.cache_data["published_videos"] and \
               video_path in self.cache_data["published_videos"][platform]
    
    def get_failed_video_info(self, platform: str, video_path: str) -> Optional[Dict]:
        """获取失败视频的信息"""
        if platform in self.cache_data["failed_videos"] and \
           video_path in self.cache_data["failed_videos"][platform]:
            return self.cache_data["failed_videos"][platform][video_path]
        return None
    
    def mark_video_published(self, platform: str, video_path: str, publish_time: datetime = None):
        """标记视频为已发布"""
        if platform not in self.cache_data["published_videos"]:
            self.cache_data["published_videos"][platform] = {}
        
        self.cache_data["published_videos"][platform][video_path] = {
            "publish_time": publish_time.isoformat() if publish_time else datetime.now().isoformat(),
            "status": "success"
        }
        
        # 如果这个视频之前在失败列表中，移除它
        if platform in self.cache_data["failed_videos"] and \
           video_path in self.cache_data["failed_videos"][platform]:
            del self.cache_data["failed_videos"][platform][video_path]
        
        self._save_cache()
        logger.info(f"✅ 已标记 {platform} 平台的视频为已发布: {Path(video_path).name}")
    
    def mark_video_failed(self, platform: str, video_path: str, 
                         scheduled_time: datetime, error_message: str = ""):
        """标记视频为发布失败"""
        if platform not in self.cache_data["failed_videos"]:
            self.cache_data["failed_videos"][platform] = {}
        
        self.cache_data["failed_videos"][platform][video_path] = {
            "scheduled_time": scheduled_time.isoformat(),
            "fail_time": datetime.now().isoformat(),
            "error_message": error_message,
            "retry_count": self.cache_data["failed_videos"][platform][video_path].get("retry_count", 0) + 1
            if video_path in self.cache_data["failed_videos"][platform] else 1
        }
        
        self._save_cache()
        logger.warning(f"❌ 已标记 {platform} 平台的视频为发布失败: {Path(video_path).name}")
    
    def get_platform_failed_videos(self, platform: str) -> List[Dict]:
        """获取指定平台失败的视频列表"""
        if platform not in self.cache_data["failed_videos"]:
            return []
        
        failed_videos = []
        for video_path, fail_info in self.cache_data["failed_videos"][platform].items():
            failed_videos.append({
                "video_path": video_path,
                "scheduled_time": datetime.fromisoformat(fail_info["scheduled_time"]),
                "fail_time": datetime.fromisoformat(fail_info["fail_time"]),
                "error_message": fail_info["error_message"],
                "retry_count": fail_info["retry_count"]
            })
        
        # 按失败时间排序
        failed_videos.sort(key=lambda x: x["fail_time"])
        return failed_videos
    
    def get_platform_published_videos(self, platform: str) -> List[Dict]:
        """获取指定平台已发布的视频列表"""
        if platform not in self.cache_data["published_videos"]:
            return []
        
        published_videos = []
        for video_path, pub_info in self.cache_data["published_videos"][platform].items():
            published_videos.append({
                "video_path": video_path,
                "publish_time": datetime.fromisoformat(pub_info["publish_time"]),
                "status": pub_info["status"]
            })
        
        # 按发布时间排序
        published_videos.sort(key=lambda x: x["publish_time"])
        return published_videos
    
    def clear_platform_cache(self, platform: str):
        """清除指定平台的缓存"""
        if platform in self.cache_data["published_videos"]:
            del self.cache_data["published_videos"][platform]
        if platform in self.cache_data["failed_videos"]:
            del self.cache_data["failed_videos"][platform]
        self._save_cache()
        logger.info(f"✅ 已清除 {platform} 平台的缓存")
    
    def clear_all_cache(self):
        """清除所有缓存"""
        self.cache_data = {
            "published_videos": {},
            "failed_videos": {},
            "last_update": None
        }
        self._save_cache()
        logger.info("✅ 已清除所有缓存")
    
    def print_cache_summary(self):
        """打印缓存摘要"""
        print("\n📊 发布缓存摘要")
        print("=" * 50)
        
        for platform in set(list(self.cache_data["published_videos"].keys()) + 
                          list(self.cache_data["failed_videos"].keys())):
            published_count = len(self.cache_data["published_videos"].get(platform, {}))
            failed_count = len(self.cache_data["failed_videos"].get(platform, {}))
            
            print(f"\n📱 {platform.upper()} 平台:")
            print(f"   ✅ 已发布: {published_count} 个视频")
            print(f"   ❌ 发布失败: {failed_count} 个视频")
            
            # 显示失败视频详情
            if failed_count > 0:
                print("   失败视频列表:")
                for video_path, fail_info in self.cache_data["failed_videos"][platform].items():
                    retry_count = fail_info.get("retry_count", 0)
                    print(f"     - {Path(video_path).name} (重试次数: {retry_count})")
        
        print(f"\n📝 最后更新: {self.cache_data.get('last_update', '从未更新')}")
        print("=" * 50)