#!/usr/bin/env python3
"""
快手统计报告生成器
生成专业的数据报告和可视化内容
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Template
from utils.log import kuaishou_logger

from .data_structures import KuaishouAnalyticsReport
from .analytics import KuaishouDataProcessor


class KuaishouReportGenerator:
    """快手统计报告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_json_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """生成JSON格式的完整数据报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kuaishou_report_{timestamp}.json"
        
        file_path = self.output_dir / filename
        
        # 添加元数据
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0',
                'source': '快手统计采集器',
                'data_size': len(data.get('video_details', []))
            },
            'data': data
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            kuaishou_logger.info(f"JSON报告已生成: {file_path}")
            return str(file_path)
        except Exception as e:
            kuaishou_logger.error(f"生成JSON报告失败: {e}")
            return ""
    
    def generate_html_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """生成美观的HTML报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kuaishou_report_{timestamp}.html"
        
        file_path = self.output_dir / filename
        
        try:
            # 键盘和处理数据
            df = pd.DataFrame(data.get('video_details', []))
            summary = data.get('account_summary', {})
            
            # 创建可视化数据
            chart_data = {
                'totalViews': summary.get('total_views', 0),
                'totalLikes': summary.get('total_likes', 0),
                'totalVideos': summary.get('total_videos', 0),
                'averageViews': round(df['views'].mean()) if not df.empty else 0,
                'averageLikes': round(df['likes'].mean()) if not df.empty else 0,
                'averageLikes': round(df['likes'].mean()) if not df.empty else 0,
                'avgLikeRate': round(df['like_rate'].mean() if not df.empty else 0, 2)
            }
            
            # 排序数据获取top视频
            top_videos = []
            if not df.empty:
                top_videos = df.nlargest(5, 'views')[['title', 'views', 'likes', 'like_rate']].to_dict('records')
            
            # 生成HTML
            html_template = self._get_html_template()
            template = Template(html_template)
            
            html_content = template.render(
                summary=summary,
                top_videos=top_videos,
                total_videos=len(data.get('video_details', [])),
                collected_at=data.get('collection_time', datetime.now().isoformat()),
                chart_data=chart_data
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            kuaishou_logger.info(f"HTML报告已生成: {file_path}")
            return str(file_path)
            
        except Exception as e:
            kuaishou_logger.error(f"生成HTML报告失败: {e}")
            return ""
    
    def generate_csv_export(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """生成CSV格式的详细数据"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kuaishou_data_{timestamp}.csv"
        
        file_path = self.output_dir / filename
        
        try:
            df = pd.DataFrame(data.get('video_details', []))
            
            if not df.empty:
                # 排序并选择关键列
                df_sorted = df.sort_values('views', ascending=False)
                
                # 确保列顺序
                columns_order = ['title', 'views', 'likes', 'comments', 'shares', 'like_rate', 'upload_time']
                
                # 按存在列保存
                existing_cols = [col for col in columns_order if col in df_sorted.columns]
                final_df = df_sorted[existing_cols]
                
                final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                kuaishou_logger.info(f"CSV数据已导出: {file_path}")
                return str(file_path)
            else:
                kuaishou_logger.warning("无数据可导出")
                return ""
                
        except Exception as e:
            kuaishou_logger.error(f"生成CSV导出失败: {e}")
            return ""
    
    def generate_markdown_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """生成Markdown格式的报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kuaishou_report_{timestamp}.md"
        
        file_path = self.output_dir / filename
        
        try:
            summary = data.get('account_summary', {})
            videos = data.get('video_details', [])
            df = pd.DataFrame(videos)
            
            report_lines = [
                f"# 📊 快手账号数据报告",
                f"\n**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n",
                "",
                "## 📈 账号概览",
                "",
                f"- **账号名称**: {summary.get('account_name', '未知')}",
                f"- **视频总数**: {summary.get('total_videos', 0)}",
                f"- **总播放量**: {summary.get('total_views', 0):,}",
                f"- **总点赞数**: {summary.get('total_likes', 0):,}",
                f"- **总评论数**: {summary.get('total_comments', 0):,}",
                f"- **总分享数**: {summary.get('total_shares', 0):,}",
                f"- **粉丝数**: {summary.get('followers', 0):,}",
                "",
                "## 🎯 视频表现分析"
            ]
            
            if not df.empty:
                # 关键指标
                report_lines.extend([
                    "",
                    f"- **平均播放量**: {df['views'].mean():.0f}",
                    f"- **平均点赞率**: {df['like_rate'].mean():.2f}%",
                    f"- **热门视频**: {len(df[df['views'] >= df['views'].quantile(0.8)])}",
                    f"- **最近30天**: {len(df)}个视频"
                ])
                
                # 最佳表现视频
                if not df.empty:
                    top_videos = df.nlargest(3, 'views')
                    report_lines.extend(["", "## ⭐ 热门视频", ""])
                    
                    for idx, (_, vid) in enumerate(top_videos.iterrows(), 1):
                        title_preview = vid['title'][:50] + "..." if len(vid['title']) > 50 else vid['title']
                        report_lines.extend([
                            f"**{idx}. {title_preview}**",
                            f"- 播放量: {vid['views']:,}",
                            f"- 点赞: {vid['likes']:,}",
                            f"- 点赞率: {vid['like_rate']:.2f}%",
                            ""
                        ])
            
            # 结论和建议
            report_lines.extend([
                "## 💡 数据洞察",
                "",
                "1. **互动表现**: 建议关注点赞率超过5%的内容"
            ])
            
            markdown_content = "\n".join(report_lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            kuaishou_logger.info(f"Markdown报告已生成: {file_path}")
            return str(file_path)
            
        except Exception as e:
            kuaishou_logger.error(f"生成Markdown报告失败: {e}")
            return ""
    
    def _get_html_template(self) -> str:
        """获取HTML报告模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>快手账号数据报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }
        h2 { color: #34495e; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.8; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: 600; }
        .generated-at { color: #7f8c8d; font-size: 0.9em; text-align: center; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 快手账号数据报告</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ summary.total_videos or 0 }}</div>
                <div class="stat-label">视频总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ "{:,}".format(summary.total_views or 0) }}</div>
                <div class="stat-label">总播放量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ "{:,}".format(summary.total_likes or 0) }}</div>
                <div class="stat-label">总点赞</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ "{:,}".format(summary.followers or 0) }}</div>
                <div class="stat-label">粉丝数</div>
            </div>
        </div>
        
        <h2>📈 视频表现</h2>
        <table>
            <thead>
                <tr>
                    <th>视频信息</th>
                    <th>播放量</th>
                    <th>点赞</th>
                    <th>点赞率</th>
                </tr>
            </thead>
            <tbody>
                {% for video in top_videos[:10] %}
                <tr>
                    <td>{{ video.title }}</td>
                    <td>{{ "{:,}".format(video.views) }}</td>
                    <td>{{ "{:,}".format(video.likes) }}</td>
                    <td>{{ video.like_rate }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <p class="generated-at">报告生成时间: {{ collected_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
        """.strip()


class ReportManager:
    """报告管理器类"""
    
    def __init__(self, base_output_dir: str = "reports/kuaishou"):
        self.base_dir = Path(base_output_dir)
        self.generators = {
            'json': KuaishouReportGenerator(self.base_dir / "json"),
            'html': KuaishouReportGenerator(self.base_dir / "html"),
            'csv': KuaishouReportGenerator(self.base_dir / "csv"),
            'markdown': KuaishouReportGenerator(self.base_dir / "markdown")
        }
    
    def generate_all_reports(self, data: Dict[str, Any], base_name: str = None) -> Dict[str, str]:
        """生成所有格式的报告"""
        if not base_name:
            base_name = f"kuaishou_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        reports = {}
        
        for format_name, generator in self.generators.items():
            try:
                if format_name == 'json':
                    reports[format_name] = generator.generate_json_report(data, f"{base_name}.json")
                elif format_name == 'html':
                    reports[format_name] = generator.generate_html_report(data, f"{base_name}.html")
                elif format_name == 'csv':
                    reports[format_name] = generator.generate_csv_export(data, f"{base_name}.csv")
                elif format_name == 'markdown':
                    reports[format_name] = generator.generate_markdown_report(data, f"{base_name}.md")
            except Exception as e:
                kuaishou_logger.error(f"生成{format_name}报告失败: {e}")
                reports[format_name] = ""
        
        return reports
    
    def generate_summary_report(self, data: Dict[str, Any]) -> str:
        """生成简洁摘要报告"""
        summary_data = {
            'account_summary': data.get('account_summary', {}),
            'key_metrics': self._calculate_key_metrics(data)
        }
        
        filename = f"kuaishou_summary_{datetime.now().strftime('%Y%m%d')}.json"
        
        generator = KuaishouReportGenerator(self.base_dir)
        return generator.generate_json_report(summary_data, filename)
    
    def _calculate_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算关键指标"""
        videos = data.get('video_details', [])
        df = pd.DataFrame(videos)
        
        if df.empty:
            return {}
        
        return {
            'total_videos': len(videos),
            'total_views': df['views'].sum() if 'views' in df.columns else 0,
            'average_views': df['views'].mean() if 'views' in df.columns else 0,
            'engagement_rate': df['like_rate'].mean() if 'like_rate' in df.columns else 0,
            'collection_date': data.get('collection_time', datetime.now().isoformat())
        }