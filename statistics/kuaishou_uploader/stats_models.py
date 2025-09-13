#!/usr/bin/env python3
"""
快手数据模型定义
定义统汁数据的标准结构，对应uploader/KsUploader需求
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


@dataclass
class KuaishouVideoStats:
    """快手单视频统计信息
    对应 uploader/ks_uploader/KSVideo 的数据返回格式
    """
    
    video_id: str = ""
    title: str = ""
    upload_time: Optional[datetime] = None
    publish_time: Optional[datetime] = None
    status: str = "normal"  # normal/under_review/deleted
    
    # 播放和互动数据
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collections: int = 0
    
    # 质量指标
    like_rate: float = 0.0      # 点赞率 (虚拟)
    comment_rate: float = 0.0   # 评论率
    share_rate: float = 0.0     # 分享率
    
    # 涨粉数据
    new_followers: int = 0
    
    # 收益数据
    earnings: Decimal = Decimal('0.00')
    cpm: Decimal = Decimal('0.00')  # 每千次播放收益
    
    # 快手special数据
    play_duration: float = 0.0  # 播放时长(秒)
    finish_rate: float = 0.0    # 完播率
    
    def calculate_rates(self):
        """计算互动率等衍生指标"""
        if self.views > 0:
            self.like_rate = round((self.likes / self.views) * 100, 2)
            self.comment_rate = round((self.comments / self.views) * 100, 2) 
            self.share_rate = round((self.shares / self.views) * 100, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'status': self.status,
            'views': self.views,
            'likes': self.likes,
            'comments': self.comments,
            'shares': self.shares,
            'collections': self.collections,
            'like_rate': self.like_rate,
            'comment_rate': self.comment_rate,
            'share_rate': self.share_rate,
            'new_followers': self.new_followers,
            'earnings': float(self.earnings),
            'cpm': float(self.cpm),
            'play_duration': self.play_duration,
            'finish_rate': self.finish_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KuaishouVideoStats':
        """从字典创建对象"""
        video = cls()
        
        video.video_id = str(data.get('video_id', ''))
        video.title = str(data.get('title', ''))
        
        # 时间处理
        if 'upload_time' in data and data['upload_time']:
            try:
                video.upload_time = datetime.fromisoformat(data['upload_time'].replace('Z', '+00:00'))
            except:
                video.upload_time = None
        
        if 'publish_time' in data and data['publish_time']:
            try:
                video.publish_time = datetime.fromisoformat(data['publish_time'].replace('Z', '+00:00'))
            except:
                video.publish_time = None
        
        video.status = data.get('status', 'normal')
        video.views = int(data.get('views', 0))
        video.likes = int(data.get('likes', 0))
        video.comments = int(data.get('comments', 0))
        video.shares = int(data.get('shares', 0))
        video.collections = int(data.get('collections', 0))
        video.new_followers = int(data.get('new_followers', 0))
        video.earnings = Decimal(str(data.get('earnings', '0.00')))
        video.cpm = Decimal(str(data.get('cpm', '0.00')))
        video.play_duration = float(data.get('play_duration', 0.0))
        video.finish_rate = float(data.get('finish_rate', 0.0))
        video.like_rate = float(data.get('like_rate', 0.0))
        video.comment_rate = float(data.get('comment_rate', 0.0))
        video.share_rate = float(data.get('share_rate', 0.0))
        
        return video


@dataclass
class KuaishouAccountStats:
    """快手账号概览数据"""
    
    account_name: str = ""
    account_id: str = ""
    
    # 核心数据
    followers: int = 0
    following: int = 0
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_collections: int = 0
    
    # 累计数据
    total_earnings: Decimal = Decimal('0.00')
    average_cpm: Decimal = Decimal('0.00')
    cumulative_watch_time: float = 0.0  # 小时
    
    # 质量评分
    active_score: float = 0.0
    content_score: float = 0.0
    engagement_score: float = 0.0
    account_health_score: float = 0.0
    
    # 元数据
    last_update: Optional[datetime] = None
    stats_collection_date: str = ""
    data_source: str = "快手创作者平台"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        self.last_update = datetime.now()
        
        return {
            'account_name': self.account_name,
            'account_id': self.account_id,
            'followers': self.followers,
            'following': self.following,
            'total_videos': self.total_videos,
            'total_views': self.total_views,
            'total_likes': self.total_likes,
            'total_comments': self.total_comments,
            'total_shares': self.total_shares,
            'total_collections': self.total_collections,
            'total_earnings': float(self.total_earnings),
            'average_cpm': float(self.average_cpm),
            'cumulative_watch_time': self.cumulative_watch_time,
            'active_score': self.active_score,
            'content_score': self.content_score,
            'engagement_score': self.engagement_score,
            'account_health_score': self.account_health_score,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'stats_collection_date': self.stats_collection_date,
            'data_source': self.data_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KuaishouAccountStats':
        """从字典创建对象"""
        stats = cls()
        
        stats.account_name = str(data.get('account_name', ''))
        stats.account_id = str(data.get('account_id', ''))
        stats.followers = int(data.get('followers', 0))
        stats.following = int(data.get('following', 0))
        stats.total_videos = int(data.get('total_videos', 0))
        stats.total_views = int(data.get('total_views', 0))
        stats.total_likes = int(data.get('total_likes', 0))
        stats.total_comments = int(data.get('total_comments', 0))
        stats.total_shares = int(data.get('total_shares', 0))
        stats.total_collections = int(data.get('total_collections', 0))
        stats.total_earnings = Decimal(str(data.get('total_earnings', '0.00')))
        stats.average_cpm = Decimal(str(data.get('average_cpm', '0.00')))
        stats.cumulative_watch_time = float(data.get('cumulative_watch_time', 0.0))
        stats.active_score = float(data.get('active_score', 0.0))
        stats.content_score = float(data.get('content_score', 0.0))
        stats.engagement_score = float(data.get('engagement_score', 0.0))
        stats.account_health_score = float(data.get('account_health_score', 0.0))
        stats.stats_collection_date = str(data.get('stats_collection_date', ''))
        stats.data_source = str(data.get('data_source', '快手创作者平台'))
        
        if 'last_update' in data and data['last_update']:
            try:
                stats.last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            except:
                stats.last_update = None
        
        return stats
    
    def calculate_health_score(self, video_stats: list = None) -> float:
        """计算综kd分"""
        score = 0.0
        
        # 关注度 (30%)
        if self.followers > 100000:
            score += 30
        elif self.followers > 10000:
            score += 20
        elif self.followers > 1000:
            score += 10
        elif self.followers > 100:
            score += 5
        
        # 播放量贡献 (30%)
        if self.total_views > 1000000:
            score += 30
        elif self.total_views > 100000:
            score += 20
        elif self.total_views > 10000:
            score += 10
        
        # 互动率贡献 (25%)
        if self.engagement_score > 5:
            score += 25
        elif self.engagement_score > 2:
            score += 15
        elif self.engagement_score > 1:
            score += 5
        
        # 活跃度 (15%)
        if self.total_videos > 100:
            score += 15
        elif self.total_videos > 50:
            score += 10
        elif self.total_videos > 10:
            score += 5
        
        self.account_health_score = min(score, 100.0)
        return self.account_health_score


@dataclass
class KuaishouPeriodStats:
    """时间段统计数据"""
    
    period_type: str = ""  # daily/weekly/monthly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # 期间数据
    videos_published: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    new_followers: int = 0
    earnings: Decimal = Decimal('0.00')
    
    # 增长率
    views_growth: float = 0.0
    followers_growth: int = 0
    
    # 最佳表现
    top_video_id: Optional[str] = None
    top_video_title: Optional[str] = None
    top_video_views: int = 0
    
    def calculate_growth(self, previous_stats: 'KuaishouPeriodStats'):
        """计算相对于前一期的增长率"""
        if previous_stats.total_views > 0:
            self.views_growth = round(
                ((self.total_views - previous_stats.total_views) / previous_stats.total_views) * 100,
                2
            )
        else:
            self.views_growth = 0.0


# 快手API接口定义
try:
    from .kuashou_api import KuaishouAPI
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

if API_AVAILABLE:
    __all__.extend(['KuaishouAPI'])