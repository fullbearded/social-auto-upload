#!/usr/bin/env python3
"""
快手数据统计CLI工具
提供命令行接口获取和分析快手账号数据
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加上级路径到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# 添加上级路径到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from conf import BASE_DIR
from .scraper import KuaishouStatisticsScraper, get_kuaishou_statistics
from .analytics import KuaishouDataProcessor
from .reporter import ReportManager, KuaishouReportGenerator
from .storage import KuaishouDataStorage


class KuaishouStatsCLI:
    """快手数据统计CLI"""
    
    def __init__(self):
        self.cookie_path = BASE_DIR / "cookies" / "ks_uploader" / "account.json"
    
    async def collect_basic_stats(self):
        """收集基本统计数据"""
        print("🚀 开始收集快手统计数据...")
        
        if not self.cookie_path.exists():
            print("❌ 找不到快手Cookie文件，请先登录获取")
            return
        
        try:
            data = await get_kuaishou_statistics(str(self.cookie_path))
            print("✅ 数据收集完成")
            return data
        except Exception as e:
            print(f"❌ 数据收集失败: {e}")
            return None
    
    async def collect_and_save(self, output_dir: str = "reports"):
        """收集并保存所有数据"""
        data = await self.collect_basic_stats()
        if not data:
            return False
        
        # 保存到数据库
        try:
            account_id = data.get('account_summary', {}).get('account_name', 'ks_account')
            storage = KuaishouDataStorage()
            
            storage.save_account_summary(data['account_summary'])
            storage.save_video_details(account_id, data['video_details'])
            
            print("✅ 数据已保存到数据库")
        except Exception as e:
            print(f"⚠️ 保存到数据库失败: {e}")
        
        # 生成多种格式报告
        report_manager = ReportManager(output_dir)
        reports = report_manager.generate_all_reports(data)
        
        print("\n📊 报告生成完成:")
        for format_name, file_path in reports.items():
            if file_path:
                print(f"   {format_name.upper()}: {file_path}")
        
        return True
    
    async def get_detailed_analysis(self):
        """获取详细分析"""
        data = await self.collect_basic_stats()
        if not data:
            return False
        
        # 数据清洗和分析
        df = pd.DataFrame(data.get('video_details', []))
        
        if df.empty:
            print("❌ 无视频数据可分析")
            return
        
        print("\n" + "="*50)
        print("📊 详细分析报告")
        print("="*50)
        
        # 基础统计
        print(f"\n🏆 基础统计:")
        print(f"   视频总数: {len(df)}")
        print(f"   总播放量: {df['views'].sum():,}")
        print(f"   总点赞数: {df['likes'].sum():,}")
        print(f"   平均播放量: {df['views'].mean():.0f}")
        print(f"   平均点赞率: {df['like_rate'].mean():.2f}%")
        
        # 热门视频
        if len(df) >= 1:
            top_videos = df.nlargest(3, 'views')
            print(f"\n🔥 热门视频 TOP3:")
            
            for idx, (_, video) in enumerate(top_videos.iterrows(), 1):
                print(f"   {idx}. {video['title'][:30]}...")
                print(f"      📺 播放量: {video['views']:,}")
                print(f"      ❤️ 点赞: {video['likes']:,}")
                print(f"      👍 点赞率: {video['like_rate']:.2f}%")
                print()
        
        # 趋势分析
        trend_data = KuaishouDataProcessor.generate_growth_analysis(df)
        if trend_data:
            print(f"📈 增长趋势:")
            recent_growth = trend_data.get('recent_growth_rate', 0)
            if recent_growth:
                print(f"   月度增长: {recent_growth}%")
        
        return True
    
    def export_data(self, format_type: str = "json"):
        """导出数据"""
        async def _export():
            storage = KuaishouDataStorage()
            account_id = "ks_account"
            
            if format_type == "json":
                output_path = BASE_DIR / "reports" / f"kuaishou_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                storage.export_to_json(account_id, str(output_path))
                print(f"✅ JSON导出完成: {output_path}")
            
            elif format_type == "csv":
                videos = storage.get_video_performance(account_id)
                output_path = BASE_DIR / "reports" / f"kuaishou_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                if videos:
                    import pandas as pd
                    df = pd.DataFrame(videos)
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                    print(f"✅ CSV导出完成: {output_path}")
                else:
                    print("❌ 无数据可导出")
        
        return asyncio.run(_export())
    
    def check_data_availability(self) -> bool:
        """检查数据可用性"""
        print("🔍 检查快手数据可用性...")
        
        if not self.cookie_path.exists():
            print("   ❌ Cookie文件不存在")
            return False
        
        print("   ✅ Cookie文件存在")
        
        # 异步验证cookie是否有效
        async def validate():
            try:
                from .scraper import KuaishouStatisticsScraper
                scraper = KuaishouStatisticsScraper(str(self.cookie_path))
                valid = await scraper.validate_cookie()
                
                print("   ✅ Cookie验证通过" if valid else "   ❌ Cookie验证失败")
                return valid
            except Exception:
                print("   ⚠️ Cookie验证错误")
                return False
        
        return asyncio.run(validate())


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="快手数据统计CLI工具")
    parser.add_argument("action", choices=["collect", "analyze", "export", "check"], 
                       help="执行的操作")
    parser.add_argument("--format", choices=["json", "csv", "html", "all"], default="json",
                       help="导出格式")
    parser.add_argument("--output", default="reports",
                       help="输出目录")
    parser.add_argument("--account", help="指定账号ID（可选）")
    
    args = parser.parse_args()
    
    cli = KuaishouStatsCLI()
    
    if args.action == "check":
        cli.check_data_availability()
    
    elif args.action == "collect":
        if args.format == "all":
            asyncio.run(cli.collect_and_save(args.output))
        else:
            asyncio.run(cli.collect_and_save(args.output))
    
    elif args.action == "analyze":
        asyncio.run(cli.get_detailed_analysis())
    
    elif args.action == "export":
        cli.export_data(args.format)


if __name__ == "__main__":
    main()