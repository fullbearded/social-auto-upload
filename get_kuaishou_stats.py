#!/usr/bin/env python3
"""
快手数据统计获取工具 - 一键使用
快速获取和分析快手账号数据
"""

import asyncio
import sys
from pathlib import Path

# 保持兼容性
parent_dir = Path(__file__).parent
sys.path.append(str(parent_dir))

from conf import BASE_DIR
from uploader.ks_uploader.statistics import get_kuaishou_statistics, ReportManager


async def main():
    """演示快速获取快手数据"""
    print("🚀 快手数据统计获取工具")
    print("=" * 50)
    
    # 设置cookie路径
    cookie_path = BASE_DIR / "cookies" / "ks_uploader" / "account.json"
    
    if not cookie_path.exists():
        print("❌ 未找到快手Cookie文件")
        print("请确保在以下路径有文件:")
        print(f"   {cookie_path}")
        print("可通过运行 python examples/get_ks_cookie.py 获取Cookie")
        return
    
    print(f"✅ 找到Cookie文件: {cookie_path}")
    
    try:
        # 获取所有数据
        print("🔄 正在收集快手账号数据...")
        data = await get_kuaishou_statistics(str(cookie_path))
        
        if not data:
            print("❌ 数据获取失败")
            return
        
        # 显示基础摘要
        summary = data.get('account_summary', {})
        videos = data.get('video_details', [])
        
        print(f"\n📊 快手账号数据摘要:")
        print(f"   账号名称: {summary.get('account_name', '未知')}")
        print(f"   视频总数: {summary.get('total_videos', 0)}")
        print(f"   总播放量: {summary.get('total_views', 0):,}")
        print(f"   总点赞数: {summary.get('total_likes', 0):,}")
        print(f"   粉丝数: {summary.get('followers', 0):,}")
        print(f"   视频详情: {len(videos)}条记录")
        
        # 生成报告
        print("📈 正在生成分析报告...")
        report_manager = ReportManager("reports/kuaishou")
        reports = report_manager.generate_all_reports(data)
        
        print("\n" + "=" * 50)
        print("✅ 报告生成完成:")
        for format_name, file_path in reports.items():
            if file_path:
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
                print(f"   {format_name.title()}: {file_path} ({file_size:,} bytes)")
        
        # 显示下一步操作
        print("\n🔧 下一步:")
        print("   • 查看 reports/kuaishou/ 目录中的文件")
        print("   • 运行命令行工具: python -m uploader.ks_uploader.statistics.kuaishou_stats_cli")
        print("   • 使用CLI工具: python get_kuaishou_stats.py analyze")
        
    except Exception as e:
        print(f"💥 运行错误: {e}")
        print("🔍 请检查网络连接和Cookie有效性")


if __name__ == "__main__":
    asyncio.run(main())