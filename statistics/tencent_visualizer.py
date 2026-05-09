#!/usr/bin/env python3
"""
腾讯视频号统计可视化报告生成器
生成JSON、HTML、Markdown格式的统计报告
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from utils.log import tencent_logger


class TencentReportManager:
    """腾讯视频号报告管理器"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir) / "tencent"
        self.ensure_output_dirs()
    
    def ensure_output_dirs(self):
        """确保输出目录存在"""
        dirs = ['json', 'html', 'markdown']
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def generate_all_reports(self, stats_data: Dict[str, Any]) -> Dict[str, str]:
        """生成所有格式的报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"tencent_stats_{timestamp}"
        
        reports = {}
        
        try:
            # JSON报告
            json_path = self.generate_json_report(stats_data, base_filename)
            if json_path:
                reports['json'] = json_path
            
            # HTML报告
            html_path = self.generate_html_report(stats_data, base_filename)
            if html_path:
                reports['html'] = html_path
            
            # Markdown报告
            md_path = self.generate_markdown_report(stats_data, base_filename)
            if md_path:
                reports['markdown'] = md_path
            
            tencent_logger.success("腾讯视频号报告生成完成")
            
        except Exception as e:
            tencent_logger.error(f"生成报告失败: {e}")
        
        return reports
    
    def generate_json_report(self, stats_data: Dict[str, Any], filename: str) -> Optional[str]:
        """生成JSON格式报告"""
        try:
            json_file = self.output_dir / "json" / f"{filename}.json"
            
            # 添加报告元数据
            report_data = {
                'metadata': {
                    'platform': '腾讯视频号',
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'data': stats_data
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            tencent_logger.info(f"JSON报告已生成: {json_file}")
            return str(json_file)
            
        except Exception as e:
            tencent_logger.error(f"生成JSON报告失败: {e}")
            return None
    
    def generate_html_report(self, stats_data: Dict[str, Any], filename: str) -> Optional[str]:
        """生成HTML格式报告"""
        try:
            html_file = self.output_dir / "html" / f"{filename}.html"
            
            # HTML模板
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯视频号统计数据报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #07C160;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #07C160;
            padding-bottom: 10px;
        }}
        .header {{
            background: linear-gradient(135deg, #07C160, #95EC69);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .account-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .platform {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card.followers {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.following {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .stat-card.likes {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        .stat-card.videos {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .info-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .info-section h3 {{
            color: #07C160;
            margin-top: 0;
            border-bottom: 2px solid #07C160;
            padding-bottom: 5px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: #07C160;
            color: white;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="account-name">{stats_data.get('account_name', '未知账号')}</div>
            <div class="platform">腾讯视频号统计数据</div>
        </div>
        
        <h1>📊 数据概览</h1>
        
        <div class="stats-grid">
            <div class="stat-card followers">
                <div class="stat-value">{self._format_number(stats_data.get('followers', 0))}</div>
                <div class="stat-label">粉丝数</div>
            </div>
            
            <div class="stat-card following">
                <div class="stat-value">{self._format_number(stats_data.get('following', 0))}</div>
                <div class="stat-label">关注数</div>
            </div>
            
            <div class="stat-card likes">
                <div class="stat-value">{self._format_number(stats_data.get('likes', 0))}</div>
                <div class="stat-label">获赞数</div>
            </div>
            
            <div class="stat-card videos">
                <div class="stat-value">{self._format_number(stats_data.get('videos_count', 0))}</div>
                <div class="stat-label">视频数</div>
            </div>
        </div>
        
        <div class="info-section">
            <h3>📈 数据分析</h3>
            <p><strong>账号健康度：</strong>{self._calculate_health_score(stats_data)}</p>
            <p><strong>活跃度评估：</strong>{self._assess_activity(stats_data)}</p>
            <p><strong>建议：</strong>{self._generate_suggestions(stats_data)}</p>
        </div>
        
        <div class="info-section">
            <h3>🔍 原始数据</h3>
            <pre>{json.dumps(stats_data.get('raw_data', {}), indent=2, ensure_ascii=False)}</pre>
        </div>
        
        <div class="timestamp">
            报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        
        <div class="footer">
            <p>由 social-auto-upload 自动生成</p>
            <p>🚀 专业社交媒体管理工具</p>
        </div>
    </div>
</body>
</html>
            """
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            tencent_logger.info(f"HTML报告已生成: {html_file}")
            return str(html_file)
            
        except Exception as e:
            tencent_logger.error(f"生成HTML报告失败: {e}")
            return None
    
    def generate_markdown_report(self, stats_data: Dict[str, Any], filename: str) -> Optional[str]:
        """生成Markdown格式报告"""
        try:
            md_file = self.output_dir / "markdown" / f"{filename}.md"
            
            md_content = f"""# 腾讯视频号统计数据报告

## 📱 账号信息
- **平台**: 腾讯视频号
- **账号名称**: {stats_data.get('account_name', '未知')}
- **数据获取时间**: {stats_data.get('timestamp', '未知')}

## 📊 数据概览

| 指标 | 数值 |
|------|------|
| 粉丝数 | {self._format_number(stats_data.get('followers', 0))} |
| 关注数 | {self._format_number(stats_data.get('following', 0))} |
| 获赞数 | {self._format_number(stats_data.get('likes', 0))} |
| 视频数 | {self._format_number(stats_data.get('videos_count', 0))} |

## 📈 数据分析

### 账号健康度
{self._calculate_health_score(stats_data)}

### 活跃度评估
{self._assess_activity(stats_data)}

### 建议
{self._generate_suggestions(stats_data)}

## 🔍 原始数据

```json
{json.dumps(stats_data.get('raw_data', {}), indent=2, ensure_ascii=False)}
```

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*由 social-auto-upload 自动生成*
            """
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            tencent_logger.info(f"Markdown报告已生成: {md_file}")
            return str(md_file)
            
        except Exception as e:
            tencent_logger.error(f"生成Markdown报告失败: {e}")
            return None
    
    def _format_number(self, number: int) -> str:
        """格式化数字显示"""
        if number >= 10000:
            return f"{number/10000:.1f}万"
        elif number >= 1000:
            return f"{number/1000:.1f}k"
        else:
            return f"{number:,}"
    
    def _calculate_health_score(self, stats_data: Dict[str, Any]) -> str:
        """计算账号健康度"""
        followers = stats_data.get('followers', 0)
        following = stats_data.get('following', 0)
        likes = stats_data.get('likes', 0)
        videos = stats_data.get('videos_count', 0)
        
        if followers == 0:
            return "需要建立粉丝基础"
        
        # 简单的健康度计算
        engagement_rate = (likes / followers * 100) if followers > 0 else 0
        follow_ratio = (following / followers * 100) if followers > 0 else 0
        
        if engagement_rate > 10:
            return "优秀 (互动率高)"
        elif engagement_rate > 5:
            return "良好 (互动率适中)"
        elif engagement_rate > 1:
            return "一般 (有提升空间)"
        else:
            return "需要提升互动率"
    
    def _assess_activity(self, stats_data: Dict[str, Any]) -> str:
        """评估活跃度"""
        followers = stats_data.get('followers', 0)
        videos = stats_data.get('videos_count', 0)
        likes = stats_data.get('likes', 0)
        
        if videos == 0:
            return "需要开始发布内容"
        
        avg_likes_per_video = likes / videos if videos > 0 else 0
        
        if avg_likes_per_video > 1000:
            return "非常活跃 (内容质量优秀)"
        elif avg_likes_per_video > 100:
            return "活跃 (内容质量良好)"
        elif avg_likes_per_video > 10:
            return "一般活跃 (保持内容更新)"
        else:
            return "需要提升内容质量"
    
    def _generate_suggestions(self, stats_data: Dict[str, Any]) -> str:
        """生成优化建议"""
        followers = stats_data.get('followers', 0)
        following = stats_data.get('following', 0)
        likes = stats_data.get('likes', 0)
        videos = stats_data.get('videos_count', 0)
        
        suggestions = []
        
        if followers < 100:
            suggestions.append("增加内容发布频率来吸引更多粉丝")
        
        if videos == 0:
            suggestions.append("开始发布第一个视频内容")
        elif videos < 10:
            suggestions.append("保持定期发布，建立内容库")
        
        if likes == 0:
            suggestions.append("优化内容质量，增加互动性")
        
        if following > followers * 2:
            suggestions.append("适当减少关注数量，专注于目标受众")
        
        if not suggestions:
            suggestions.append("保持当前的内容策略，继续优化内容质量")
        
        return "；".join(suggestions)


# 兼容性别名
TencentWeixinReportManager = TencentReportManager


def generate_tencent_report(stats_data: Dict[str, Any], output_dir: str = "reports") -> Dict[str, str]:
    """
    生成腾讯视频号统计报告的便捷函数
    
    Args:
        stats_data: 统计数据
        output_dir: 输出目录
    
    Returns:
        生成的报告文件路径字典
    """
    manager = TencentReportManager()
    return manager.generate_all_reports(stats_data)


if __name__ == "__main__":
    # 测试报告生成
    test_data = {
        'platform': 'tencent',
        'account_name': '测试账号',
        'followers': 12345,
        'following': 678,
        'likes': 89012,
        'videos_count': 23,
        'timestamp': datetime.now().isoformat(),
        'raw_data': {'test': 'data'}
    }
    
    manager = TencentReportManager()
    reports = manager.generate_all_reports(test_data)
    
    print("生成的报告:")
    for format_name, file_path in reports.items():
        print(f"   {format_name}: {file_path}")