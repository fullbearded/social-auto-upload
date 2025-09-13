#!/usr/bin/env python3
"""
快手数据统计数据结构定义
定义账号数据、视频数据、统计指标的标准格式
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


@dataclass
class KuaishouVideoStats:
    """单个视频的详细统计信息"""
    video_id: str = ""
    title: str = ""
    upload_time: datetime = None
    publish_time: datetime = None
    status: str = "normal"  # normal/under_review/deleted
    
    # 播放数据
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collections: int = 0
    
    # 完播数据
    finish_rate: float = 0.0  # 完播率
    avg_watch_time: float = 0.0  # 平均观看时长(秒)
    
    # 互动数据
    like_rate: float = 0.0      # 点赞率
    comment_rate: float = 0.0   # 评论率
    share_rate: float = 0.0     # 分享率
    
    # 涨粉数据
    new_followers: int = 0
    
    # 货币化数据
    earnings: Decimal = Decimal('0.00')
    cpm: Decimal = Decimal('0.00')
    
    def calculate_rates(self):
        """计算互动率等衍生指标"""
        if self.views > 0:
            self.like_rate = self.likes / self.views * 100
            self.comment_rate = self.comments / self.views * 100
            self.share_rate = self.shares / self.views * 100


@dataclass
class KuaishouAccountSummary:
    """快手账号概览统计"""
    account_name: str = ""
    account_id: str = ""
    
    # 基础数据
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_collections: int = 0
    
    # 关注数据
    followers: int = 0
    following: int = 0
    
    # 累计数据
    total_earnings: Decimal = Decimal('0.00')
    cumulative_watch_time: float = 0.0  # 累计观看时长(小时)
    
    # 时间范围
    last_update: datetime = None
    statistics_date: str = ""


@dataclass
class KuaishouPeriodStats:
    """时间段统计"""
    period_type: str = ""  # daily/weekly/monthly
    start_date: datetime = None
    end_date: datetime = None
    
    # 期间数据
    videos_published: int = 0
    total_views: int = 0
    total_likes: int = 0
    
    # 增长趋势
    views_growth: float = 0.0  # 增长率(%)
    followers_growth: int = 0
    
    # 最佳表现
    top_video: Optional[str] = None
    top_video_views: int = 0


@dataclass
class KuaishouAnalyticsReport:
    """完整的数据分析报告"""
    account_summary: KuaishouAccountSummary = field(default_factory=KuaishouAccountSummary)
    recent_videos: List[KuaishouVideoStats] = field(default_factory=list)
    daily_stats: List[KuaishouPeriodStats] = field(default_factory=list)
    weekly_stats: List[KuaishouPeriodStats] = field(default_factory=list)
    monthly_stats: List[KuaishouPeriodStats] = field(default_factory=list)
    
    # 质量指标
    active_score: float = 0.0  # 活跃度评分
    content_score: float = 0.0  # 内容质量评分
    engagement_score: float = 0.0  # 互动质量评分
    
    # 异常预警
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def generate_insights(self):
        """生成数据洞察和建议"""
        if not self.recent_videos:
            return
            
        # 计算平均表现
        avg_views = sum(v.views for v in self.recent_videos) / len(self.recent_videos)
        avg_likes = sum(v.likes for v in self.recent_videos) / len(self.recent_videos)
        
        # 质量评分
        if avg_likes > 0 and avg_views > 0:
            self.engagement_score = (avg_likes / avg_views) * 100
        
        # 活跃度评分 (基于发布频率)
        days_diff = (datetime.now() - min(
            v.publish_time for v in self.recent_videos if v.publish_time
        )).days
        
        if days_diff > 0:
            publish_freq = len(self.recent_videos) / days_diff
            self.active_score = min(publish_freq * 10, 100)  # 每天0.1条以上算优质
        
        # 生成建议
        if self.engagement_score < 2:
            self.recommendations.append("建议优化视频标题和封面，提升互动率")
        if self.active_score < 30:
            self.recommendations.append("建议保持稳定的发布频率")


# API响应数据结构
@dataclass
class KuaishouAPIResponse:
    """快手API响应的标准格式"""
    success: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# 配置类
class KuaishouEndpoints:
    """快手关键接口"""
    BASE_URL = "https://cp.kuaishou.com"
    
    # 统计相关接口
    WORKS_STATISTICS = f"{BASE_URL}/statistics/works"
    OVERVIEW = f"{BASE_URL}/statistics/overview"
    DETAIL_DASHBOARD = f"{BASE_URL}/statistics/detail"
    FAN_DATA = f"{BASE_URL}/statistics/fan"
    INCOME_DATA = f"{BASE_URL}/statistics/income"
    
    # 内容管理
    CONTENT_LIST = f"{BASE_URL}/article/manage/video"
    CONTENT_ANALYTICS = f"{BASE_URL}/article/analytics"


# 导出类列表
__all__ = [
    'KuaishouVideoStats',
    'KuaishouAccountSummary', 
    'KuaishouPeriodStats',
    'KuaishouAnalyticsReport',
    'KuaishouAPIResponse',
    'KuaishouEndpoints'
]