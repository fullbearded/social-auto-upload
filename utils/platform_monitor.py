"""
跨平台监控和分析系统
Cross-platform monitoring and analytics system

功能：
- 实时上传状态监控
- 平台响应API监控
- 风控事件检测和记录
- 上传成功率分析
- 性能指标统计
"""

import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass, asdict


@dataclass
class UploadEvent:
    """上传事件数据模型"""
    platform: str
    video_file: str
    timestamp: datetime
    success: bool
    response_time: float
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    risk_trigger: Optional[str] = None
    retry_count: int = 0
    upload_delay: float = 0.0
    platform_limits: Optional[Dict] = None


class PlatformMonitor:
    """跨平台监控系统"""
    
    def __init__(self, logs_dir: str):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 初始化事件存储
        self.events: List[UploadEvent] = []
        self.platform_stats = {}
        
        # 设置日志
        self.logger = logging.getLogger('platform_monitor')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理程序
        log_file = self.logs_dir / f"platform_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 格式化程序
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

    def record_event(self, event: UploadEvent):
        """记录上传事件"""
        self.events.append(event)
        
        # 更新平台统计
        platform = event.platform
        if platform not in self.platform_stats:
            self.platform_stats[platform] = {
                'total_uploads': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'risk_triggers': 0,
                'avg_response_time': 0,
                'avg_retry_count': 0
            }
        
        stats = self.platform_stats[platform]
        stats['total_uploads'] += 1
        
        if event.success:
            stats['successful_uploads'] += 1
        else:
            stats['failed_uploads'] += 1
        
        if event.risk_trigger:
            stats['risk_triggers'] += 1
        
        # 计算平均响应时间
        all_response_times = [e.response_time for e in self.events 
                            if e.platform == platform]
        stats['avg_response_time'] = sum(all_response_times) / len(all_response_times)
        
        # 计算平均重试次数
        all_retry_counts = [e.retry_count for e in self.events 
                          if e.platform == platform and e.retry_count > 0]
        if all_retry_counts:
            stats['avg_retry_count'] = sum(all_retry_counts) / len(all_retry_counts)
        
        self.logger.info(f"事件记录: {asdict(event)}")

    def detect_risk_patterns(self) -> List[Dict]:
        """
        检测风险模式
        
        Returns:
            List[Dict]: 检测到的风险模式列表
        """
        patterns = []
        
        for platform in self.platform_stats:
            stats = self.platform_stats[platform]
            
            # 失败率检测
            if stats['total_uploads'] >= 5:  # 至少5次上传后才分析
                failure_rate = stats['failed_uploads'] / stats['total_uploads']
                if failure_rate > 0.3:  # 失败率超过30%
                    patterns.append({
                        'type': 'high_failure_rate',
                        'platform': platform,
                        'failure_rate': failure_rate,
                        'threshold': 0.3,
                        'recommendation': '降低上传频率，检查账号状态'
                    })
            
            # 风控触发检测
            if stats['risk_triggers'] > 2:  # 一天内触发多次风控
                patterns.append({
                    'type': 'excessive_risk_triggers',
                    'platform': platform,
                    'triggers': stats['risk_triggers'],
                    'threshold': 2,
                    'recommendation': '暂停上传，等待账号冷却'
                })
            
            # 响应时间异常检测
            if stats['avg_response_time'] > 30:  # 平均响应时间超过30秒
                patterns.append({
                    'type': 'slow_response_time',
                    'platform': platform,
                    'avg_response_time': stats['avg_response_time'],
                    'threshold': 30,
                    'recommendation': '检查网络连接和平台稳定性'
                })
        
        return patterns

    def get_upload_summary(self, hours_back: int = 24) -> Dict:
        """
        获取上传摘要
        
        Args:
            hours_back: 回顾时间（小时）
            
        Returns:
            Dict: 上传摘要
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        summary = {}
        for platform in set(e.platform for e in recent_events):
            platform_events = [e for e in recent_events if e.platform == platform]
            
            summary[platform] = {
                'total_uploads': len(platform_events),
                'success_rate': len([e for e in platform_events if e.success]) / len(platform_events),
                'avg_response_time': sum(e.response_time for e in platform_events) / len(platform_events),
                'peak_hours': self._get_peak_hours(platform_events),
                'common_errors': self._get_common_errors(platform_events)
            }
        
        return summary

    def _get_peak_hours(self, events: List[UploadEvent]) -> List[int]:
        """获取高峰时段"""
        hour_counts = {}
        for event in events:
            hour = event.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # 排序并返回前3个小时
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    def _get_common_errors(self, events: List[UploadEvent]) -> List[Dict]:
        """获取常见错误"""
        error_counts = {}
        for event in events:
            if not event.success and event.error_code:
                error_key = f"{event.error_code}: {event.error_message or 'Unknown'}"
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        # 排序并返回前5个错误
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'error': error, 'count': count} for error, count in sorted_errors[:5]]

    def generate_report(self, output_format: str = 'json') -> str:
        """
        生成监控报告
        
        Args:
            output_format: 输出格式 ['json', 'csv', 'html']
            
        Returns:
            str: 报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            return self._generate_json_report(timestamp)
        elif output_format == 'csv':
            return self._generate_csv_report(timestamp)
        elif output_format == 'html':
            return self._generate_html_report(timestamp)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_json_report(self, timestamp: str) -> str:
        """生成JSON格式报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'platform_stats': self.platform_stats,
            'risk_patterns': self.detect_risk_patterns(),
            'upload_summary': self.get_upload_summary(),
            'recent_events': [asdict(event) for event in self.events[-100:]]  # 最近100个事件
        }
        
        report_file = self.logs_dir / f"monitor_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_file)

    def _generate_csv_report(self, timestamp: str) -> str:
        """生成CSV格式报告"""
        report_file = self.logs_dir / f"monitor_report_{timestamp}.csv"
        
        with open(report_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['platform', 'video_file', 'timestamp', 'success', 'response_time', 
                         'error_code', 'error_message', 'risk_trigger', 'retry_count']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in self.events:
                event_dict = asdict(event)
                # Convert datetime to string for CSV
                event_dict['timestamp'] = str(event_dict['timestamp'])
                writer.writerow(event_dict)
        
        return str(report_file)

    def _generate_html_report(self, timestamp: str) -> str:
        """生成HTML格式报告"""
        report_file = self.logs_dir / f"monitor_report_{timestamp}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>多平台上传监控报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }}
                .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>多平台上传监控报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>平台统计</h2>
            <table>
                <tr>
                    <th>平台</th>
                    <th>总上传</th>
                    <th>成功</th>
                    <th>失败</th>
                    <th>成功率</th>
                    <th>风控事件</th>
                </tr>
        """
        
        for platform, stats in self.platform_stats.items():
            success_rate = stats['successful_uploads'] / stats['total_uploads'] * 100
            html_content += f"""
                <tr>
                    <td>{platform}</td>
                    <td>{stats['total_uploads']}</td>
                    <td>{stats['successful_uploads']}</td>
                    <td>{stats['failed_uploads']}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{stats['risk_triggers']}</td>
                </tr>
            """
        
        # 风险模式检测
        risk_patterns = self.detect_risk_patterns()
        if risk_patterns:
            html_content += """
                </table>
                <h2>⚠️ 风险警告</h2>
                <div class="alert">
            """
            for pattern in risk_patterns:
                html_content += f"""
                    <p><strong>平台 {pattern['platform']}</strong></p>
                    <p>类型: {pattern['type']}</p>
                    <p>数值: {pattern.get('failure_rate', pattern.get('triggers', 'N/A'))}</p>
                    <p>建议: {pattern['recommendation']}</p>
                    <hr>
                """
            html_content += "</div>"
        
        html_content += """
            </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)

    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        if not self.events:
            return {}
        
        metrics = {'platforms': {} }
        
        for platform in set(e.platform for e in self.events):
            platform_events = [e for e in self.events if e.platform == platform]
            
            response_times = [e.response_time for e in platform_events]
            upload_delays = [e.upload_delay for e in platform_events]
            
            metrics['platforms'][platform] = {
                'avg_response_time': sum(response_times) / len(response_times),
                'max_response_time': max(response_times),
                'min_response_time': min(response_times),
                'avg_upload_delay': sum(upload_delays) / len(upload_delays) if upload_delays else 0,
                'success_rate': len([e for e in platform_events if e.success]) / len(platform_events),
                'avg_retries': sum(e.retry_count for e in platform_events) / len(platform_events)
            }
        
        return metrics

    def export_for_analysis(self, file_path: str) -> str:
        """导出数据用于分析"""
        # 转换所有事件为可序列化格式
        export_data = {
            'events': [],
            'stats': self.platform_stats,
            'export_time': datetime.now().isoformat()
        }
        
        for event in self.events:
            event_dict = asdict(event)
            event_dict['timestamp'] = str(event_dict['timestamp'])
            export_data['events'].append(event_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"数据导出完成: {file_path}")
        return file_path


def create_platform_monitor(logs_dir: str = None) -> PlatformMonitor:
    """
    创建平台监控器
    
    Args:
        logs_dir: 日志目录
        
    Returns:
        PlatformMonitor: 监控器实例
    """
    if logs_dir is None:
        from conf import BASE_DIR
        logs_dir = Path(BASE_DIR) / "logs"
    
    return PlatformMonitor(str(logs_dir))