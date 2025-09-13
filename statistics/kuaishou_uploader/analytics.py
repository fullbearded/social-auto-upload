#!/usr/bin/env python3
"""
快手数据分析和报告生成器
提供数据清洗、分析洞察和可视化报告
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal
import hashlib

from .data_structures import (
    KuaishouVideoStats, 
    KuaishouAccountSummary,
    KuaishouPeriodStats,
    KuaishouAnalyticsReport,
    KuaishouAPIResponse
)
from utils.log import kuaishou_logger


class KuaishouDataProcessor:
    """快手数据处理器"""
    
    @staticmethod
    def clean_and_validate_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗和验证原始数据"""
        cleaned_data = {
            'account_summary': raw_data.get('account_summary', {}),
            'video_details': [],
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'original_size': len(raw_data.get('video_details', [])),
                'validation_status': 'valid'
            }
        }
        
        # 清洗视频数据
        for video in raw_data.get('video_details', []):
            cleaned_video = KuaishouDataProcessor._clean_single_video(video)
            if cleaned_video:
                cleaned_video['validation_status'] = 'cleaned'
                cleaned_data['video_details'].append(cleaned_video)
            else:
                cleaned_data['metadata']['validation_status'] = 'partial'
        
        cleaned_data['metadata']['cleaned_size'] = len(cleaned_data['video_details'])
        return cleaned_data
    
    @staticmethod
    def _clean_single_video(video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """清洗单个视频数据"""
        try:
            cleaned = {
                'video_id': str(video_data.get('video_id', '')).strip(),
                'title': str(video_data.get('title', '')).strip()[:200],  # 限制标题长度
                'views': int(video_data.get('views', 0)),
                'likes': int(video_data.get('likes', 0)),
                'comments': int(video_data.get('comments', 0)),
                'shares': int(video_data.get('shares', 0)),
                'collections': int(video_data.get('collections', 0)),
                'new_followers': int(video_data.get('new_followers', 0)),
                'earnings': Decimal(str(video_data.get('earnings', '0'))),
                'upload_time': video_data.get('upload_time'),
                'status': video_data.get('status', 'normal')
            }
            
            # 计算额外指标
            total_views = cleaned['views']
            if total_views > 0:
                cleaned['like_rate'] = round(cleaned['likes'] / total_views * 100, 2)
                cleaned['comment_rate'] = round(cleaned['comments'] / total_views * 100, 2)
                cleaned['share_rate'] = round(cleaned['shares'] / total_views * 100, 2)
                cleaned['collection_rate'] = round(cleaned['collections'] / total_views * 100, 2)
            else:
                cleaned.update({'like_rate': 0.0, 'comment_rate': 0.0, 'share_rate': 0.0, 'collection_rate': 0.0})
            
            return cleaned
            
        except Exception as e:
            kuaishou_logger.warning(f"视频数据清洗失败: {e}")
            return None
    
    @staticmethod
    def generate_performance_analysis(df: pd.DataFrame, account_summary: Dict) -> Dict[str, Any]:
        """生成性能分析"""
        if df.empty:
            return {'error': '无数据可分析'}
        
        # 基础统计数据
        total_videos = len(df)
        total_views = df['views'].sum()
        total_likes = df['likes'].sum()
        
        # 统计摘要
        stats = {
            'overview': {
                'total_videos': int(total_videos),
                'total_views': int(total_views),
                'total_likes': int(total_likes),
                'average_per_video': {
                    'views': round(df['views'].mean(), 2),
                    'likes': round(df['likes'].mean(), 2),
                    'comments': round(df['comments'].mean(), 2),
                    'shares': round(df['shares'].mean(), 2)
                }
            },
            'percentile_analysis': {
                'top_10_percentile': {
                    'views_threshold': float(df['views'].quantile(0.9)),
                    'videos_count': int(len(df[df['views'] >= df['views'].quantile(0.9)]))
                },
                'median_stats': {
                    'views': float(df['views'].quantile(0.5)),
                    'likes': float(df['likes'].quantile(0.5))
                }
            },
            'interaction_rates': {
                'average_like_rate': round(df['like_rate'].mean(), 2),
                'average_comment_rate': round(df['comment_rate'].mean(), 2),
                'good_performance_threshold': 5.0  # 优质的互动率阈值
            }
        }
        
        return stats
    
    @staticmethod
    def identify_trending_videos(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """识别优质/热门视频"""
        if df.empty:
            return []
        
        # 定义热门视频标准
        threshold_views = df['views'].quantile(0.8)
        threshold_likes = df['likes'].quantile(0.8)
        threshold_rate = df['like_rate'].quantile(0.8)
        
        trending = df[
            (df['views'] >= threshold_views) | 
            (df['likes'] >= threshold_likes) |
            (df['like_rate'] >= threshold_rate)
        ].copy()
        
        trending_videos = []
        for _, video in trending.iterrows():
            trending_videos.append({
                'video_id': str(video.get('video_id', '')),
                'title': str(video.get('title', ''))[:30] + "..." if len(str(video.get('title', ''))) > 30 else str(video.get('title', '')),
                'views': int(video['views']),
                'likes': int(video['likes']),
                'like_rate': float(video['like_rate']),
                'performance': 'high' if video['views'] >= df['views'].quantile(0.95) else 'medium'
            })
        
        return sorted(trending_videos, key=lambda x: x['views'], reverse=True)[:10]
    
    @staticmethod
    def calculate_content_insights(df: pd.DataFrame) -> Dict[str, Any]:
        """计算内容洞察"""
        if df.empty:
            return {}
        
        # 最佳发布时间分析
        df['upload_time'] = pd.to_datetime(df['upload_time'], errors='coerce')
        df_hour = df.dropna(subset=['upload_time']).copy()
        
        if not df_hour.empty:
            df_hour['hour'] = df_hour['upload_time'].dt.hour
            hourly_performance = df_hour.groupby('hour')['views'].mean().round(2)
            best_hours = hourly_performance.nlargest(3).to_dict()
        else:
            best_hours = {}
        
        # 内容长度分析
        df['title_length'] = df['title'].str.len()
        title_insights = {
            'avg_length': float(df['title_length'].mean()),
            'short_titles': int(len(df[df['title_length'] <= 20])),
            'long_titles': int(len(df[df['title_length'] > 50]))
        }
        
        # 标题关键词分析
        title_words = ' '.join(df['title']).lower().split()
        from collections import Counter
        common_words = dict(Counter(title_words).most_common(20))
        
        return {
            'best_upload_hours': best_hours,
            'title_insights': title_insights,
            'common_keywords': common_words
        }
    
    @staticmethod
    def generate_growth_analysis(df: pd.DataFrame, period_days: int = 30) -> Dict[str, Any]:
        """生成增长趋势分析"""
        if df.empty:
            return {}
        
        df['upload_time'] = pd.to_datetime(df['upload_time'], errors='coerce')
        df_clean = df.dropna(subset=['upload_time']).copy()
        
        if df_clean.empty:
            return {}
        
        # 按月统计
        df_clean['month'] = df_clean['upload_time'].dt.to_period('M')
        monthly_stats = df_clean.groupby('month').agg({
            'views': 'sum',
            'likes': 'sum',
            'upload_time': 'count'
        }).round(2)
        monthly_stats.columns = ['total_views', 'total_likes', 'video_count']
        
        # 计算增长率（如果有足够的数据）
        monthly_stats = monthly_stats.sort_index()
        if len(monthly_stats) >= 2:
            recent_month = monthly_stats.iloc[-1]
            previous_month = monthly_stats.iloc[-2]
            growth_rate = round(((recent_month['total_views'] - previous_month['total_views']) / previous_month['total_views']) * 100, 2)
        else:
            growth_rate = 0.0
        
        return {
            'monthly_summary': monthly_stats.round(2).to_dict(),
            'recent_growth_rate': growth_rate,
            'trend_direction': 'up' if growth_rate > 0 else 'down' if growth_rate < 0 else 'stable'
        }
    
    @staticmethod
    def generate_recommendations(df: pd.DataFrame, account_summary: Dict) -> Dict[str, List[str]]:
        """生成优化建议"""
        recommendations = {
            'content_strategy': [],
            'posting_schedule': [],
            'engagement_optimization': []
        }
        
        if df.empty:
            return recommendations
        
        # 内容策略建议
        avg_views = df['views'].mean()
        avg_like_rate = df['like_rate'].mean()
        
        if avg_like_rate < 2:
            recommendations['content_strategy'].append(
                "视频互动率较低（低于2%），建议优化标题和封面，提升内容吸引力"
            )
        
        if avg_views < 1000:
            recommendations['content_strategy'].append(
                "平均播放量偏低（低于1000），建议参考热门视频，提升内容质量"
            )
        
        # 发布时段建议
        df_clean = df.dropna(subset=['upload_time'])
        if not df_clean.empty:
            df_clean['hour'] = pd.to_datetime(df_clean['upload_time']).dt.hour
            hourly_perf = df_clean.groupby('hour')['views'].mean()
            best_hours = list(hourly_perf.sort_values(ascending=False).head(3).index)
            recommendations['posting_schedule'].append(
                f"建议最佳发布时间：{', '.join([f'{h}:00' for h in best_hours])}"
            )
        
        # 互动优化建议
        high_performers = df[
            (df['views'] >= df['views'].quantile(0.8)) &
            (df['like_rate'] >= 5.0)
        ]
        
        if len(high_performers) > 0:
            recommendations['engagement_optimization'].append(
                f"分析{len(high_performers)}个高表现视频的成功因素，复制成功经验"
            )
        
        return recommendations