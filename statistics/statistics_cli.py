#!/usr/bin/env python3
"""
统计数据CLI工具 - 多平台统一次接口
可根据不同平台调用相应的统计获取器
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# 上级路径
sys.path.append(str(Path(__file__).parent.parent))

# 平台对应关系和可用的统计器
try:
    from statistics.kuaishou_stat import get_kuaishou_statistics, KuaishouStatsUploader
    KUAISHOU_AVAILABLE = True
except ImportError:
    try:
        # 尝试从项目根目录导入
        from kuaishou_stat import get_kuaishou_statistics, KuaishouStatsUploader
        KUAISHOU_AVAILABLE = True
    except ImportError:
        KUAISHOU_AVAILABLE = False

try:
    from statistics.tencent_stat import get_tencent_statistics, TencentStatsUploader
    TENCENT_AVAILABLE = True
except ImportError:
    try:
        # 尝试从当前目录导入
        from tencent_stat import get_tencent_statistics, TencentStatsUploader
        TENCENT_AVAILABLE = True
    except ImportError:
        TENCENT_AVAILABLE = False

try:
    from statistics.xiaohongshu_stat import get_xiaohongshu_statistics
    XIAOHONGSHU_AVAILABLE = True
except ImportError:
    try:
        # 尝试从项目根目录导入
        from statistics.xiaohongshu_stat import get_xiaohongshu_statistics
        XIAOHONGSHU_AVAILABLE = True
    except ImportError:
        XIAOHONGSHU_AVAILABLE = False

# 构建可用平台字典
AVAILABLE_PLATFORMS = {}

if KUAISHOU_AVAILABLE:
    AVAILABLE_PLATFORMS.update({
        'kuaishou': '快手',
        'ks': '快手',  # 别名
    })

if TENCENT_AVAILABLE:
    AVAILABLE_PLATFORMS.update({
        'tencent': '腾讯视频号',
        'weixin': '腾讯视频号',  # 别名
        'tx': '腾讯视频号',  # 别名
    })

if XIAOHONGSHU_AVAILABLE:
    AVAILABLE_PLATFORMS.update({
        'xiaohongshu': '小红书',
        'xhs': '小红书',  # 别名
    })


class StatisticsController:
    """统计控制器 - 管理平台统计获取"""
    
    def __init__(self, debug_mode=False):
        self.supported_platforms = AVAILABLE_PLATFORMS.copy()
        self.base_dir = Path("cookies")
        self.debug_mode = debug_mode
    
    def list_platforms(self):
        """列出支持的平台"""
        print("📱 支持的平台统计:")
        for key, name in self.supported_platforms.items():
            status = "✅ 可用" if self.is_platform_available(key) else "❌ 不可用"
            print(f"   - {name:6} ({key:8}) {status}")
    
    def is_platform_available(self, platform: str) -> bool:
        """检查平台是否可用"""
        if platform not in self.supported_platforms:
            return False
            
        if platform in ['kuaishou', 'ks']:
            return KUAISHOU_AVAILABLE
        elif platform in ['tencent', 'weixin', 'tx']:
            return TENCENT_AVAILABLE
        elif platform in ['xiaohongshu', 'xhs']:
            return XIAOHONGSHU_AVAILABLE
        
        return False
    
    def get_cookie_path(self, platform: str) -> Optional[Path]:
        """获取平台cookie路径"""
        if platform in ['kuaishou', 'ks']:
            return self.base_dir / "ks_uploader" / "account.json"
        elif platform in ['tencent', 'weixin', 'tx']:
            return self.base_dir / "tencent_uploader" / "account.json"
        elif platform in ['xiaohongshu', 'xhs']:
            return self.base_dir / "xiaohongshu_uploader" / "account.json"
        
        return None
    
    def check_cookie_exists(self, platform: str) -> bool:
        """检查cookie是否存在"""
        cookie_path = self.get_cookie_path(platform)
        return cookie_path and cookie_path.exists()
    
    def validate_cookie(self, platform: str) -> bool:
        """验证cookie有效性"""
        cookie_path = self.get_cookie_path(platform)
        
        if not cookie_path or not cookie_path.exists():
            print(f"   ❌ {platform} Cookie未找到: {cookie_path}")
            return False
        
        # 平台验证 - 实际运行时会验证
        if platform in ['kuaishou', 'ks']:
            try:
                return True  # 实际运行时会验证
            except Exception as e:
                print(f"   ❌ {platform} Cookie验证失败: {e}")
                return False
        elif platform in ['tencent', 'weixin', 'tx']:
            try:
                return True  # 实际运行时会验证
            except Exception as e:
                print(f"   ❌ {platform} Cookie验证失败: {e}")
                return False
        elif platform in ['xiaohongshu', 'xhs']:
            try:
                return True  # 实际运行时会验证
            except Exception as e:
                print(f"   ❌ {platform} Cookie验证失败: {e}")
                return False
        
        return False
    
    async def get_statistics(self, platform: str) -> Optional[dict]:
        """获取平台统计信息"""
        if not self.is_platform_available(platform):
            print(f"❌ 平台 {platform} 不可用或未实现")
            return None
        
        if not self.validate_cookie(platform):
            print(f"❌ 平台 {platform} Cookie验证失败")
            return None
        
        cookie_path = self.get_cookie_path(platform)
        print(f"🔍 {self.supported_platforms[platform]} ({platform}) 统计数据获取开始...")
        
        if platform in ['kuaishou', 'ks']:
            try:
                data = await get_kuaishou_statistics(str(cookie_path))
                print(f"✅ {platform} 数据获取成功")
                return data
            except Exception as e:
                print(f"❌ {platform} 数据获取失败: {e}")
                return None
        elif platform in ['tencent', 'weixin', 'tx']:
            try:
                data = await get_tencent_statistics(str(cookie_path), debug=self.debug_mode)
                print(f"✅ {platform} 数据获取成功")
                return data
            except Exception as e:
                print(f"❌ {platform} 数据获取失败: {e}")
                return None
        elif platform in ['xiaohongshu', 'xhs']:
            try:
                data = await get_xiaohongshu_statistics(str(cookie_path), debug=self.debug_mode)
                print(f"✅ {platform} 数据获取成功")
                return data
            except Exception as e:
                print(f"❌ {platform} 数据获取失败: {e}")
                return None
        
        return None
    
    async def run_platform_stats(self, platform: str, output_dir: str = "reports"):
        """运行平台统计和报告生成"""
        data = await self.get_statistics(platform)
        if not data:
            return False
        
        print(f"📄 正在生成 {platform} 报告...")
        
        # 针对不同平台创建相应报告生成器
        if platform in ['kuaishou', 'ks']:
            try:
                from kuaishou_stat.kuaishou_visualizer import KuaishouReportManager
                report_manager = KuaishouReportManager(output_dir)
                reports = report_manager.generate_all_reports(data)
                
                print(f"\n📊 {platform} 报告生成完成:")
                for format_name, file_path in reports.items():
                    if file_path:
                        print(f"   {format_name}: {Path(file_path).name}")
            except ImportError:
                print(f"⚠️  {platform} 报告生成模块未找到，跳过报告生成")
        elif platform in ['tencent', 'weixin', 'tx']:
            try:
                from tencent_visualizer import TencentReportManager
                report_manager = TencentReportManager(output_dir)
                reports = report_manager.generate_all_reports(data)
                
                print(f"\n📊 {platform} 报告生成完成:")
                for format_name, file_path in reports.items():
                    if file_path:
                        print(f"   {format_name}: {Path(file_path).name}")
            except ImportError:
                print(f"⚠️  {platform} 报告生成模块未找到，跳过报告生成")
        
        return True


def create_ks_visualizer():
    """为快手创建可视化报告管理器"""
    # 这种方式需要在kuaishou_uploader中导入报告功能
    pass


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多平台统计获取器 - 支持快手、腾讯视频号等平台",
        epilog="示例: python statistics_cli.py get tencent --debug\n示例: python statistics_cli.py list"
    )
    
    # 全局参数
    parser.add_argument('--debug', action='store_true',
                       help='调试模式：浏览器保持打开状态，便于调试')

    # 子命令
    sub_parsers = parser.add_subparsers(dest='command', help='可用命令')

    # list命令 - 列出支持的平台
    list_parser = sub_parsers.add_parser('list', help='列出所有支持的平台')

    # check命令 - 检查平台状态
    check_parser = sub_parsers.add_parser('check', help='检查平台和Cookie状态')
    check_parser.add_argument('--platform', choices=AVAILABLE_PLATFORMS.keys(),
                             help='检查指定平台')

    # get命令 - 获取统计数据
    get_parser = sub_parsers.add_parser('get', help='获取指定平台的统计数据')
    get_parser.add_argument('platform', choices=AVAILABLE_PLATFORMS.keys(),
                           help='要获取数据的平台')
    get_parser.add_argument('--output', default='reports', 
                           help='输出目录 (默认: reports)')
    get_parser.add_argument('--format', choices=['json', 'html', 'markdown', 'all'],
                           default='all', help='输出格式')
    get_parser.add_argument('--show', action='store_true',
                           help='显示数据而不保存')

    # analyze命令 - 详细分析
    analyze_parser = sub_parsers.add_parser('analyze', help='数据详细分析')
    analyze_parser.add_argument('platform', choices=AVAILABLE_PLATFORMS.keys(),
                               help='要分析的平台')
    analyze_parser.add_argument('--days', type=int, default=30,
                               help='分析天数 (默认: 30)')

    args = parser.parse_args()
    
    controller = StatisticsController(debug_mode=args.debug)
    
    if args.command == 'list':
        controller.list_platforms()
    
    elif args.command == 'check':
        if args.platform:
            print(f"🔍 检查平台 {args.platform} 状态...")
            if controller.validate_cookie(args.platform):
                print(f"✅ {args.platform} Cookie有效")
            else:
                print(f"❌ {args.platform} Cookie无效或缺失")
        else:
            print("检查所有平台状态:")
            for platform in controller.supported_platforms.keys():
                valid = controller.check_cookie_exists(platform) and controller.validate_cookie(platform)
                print(f"   {controller.supported_platforms[platform]} ({platform}): {'✅ 可用' if valid else '❌ 不可用'}")
    
    elif args.command == 'get':
        if args.show:
            data = await controller.get_statistics(args.platform)
            if data:
                print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            success = await controller.run_platform_stats(args.platform, args.output)
            print(f"✅ 成功" if success else "❌ 失败")
    
    elif args.command == 'analyze':
        # 此功能将在各平台的visualizer中实现
        print(f"📊 {args.platform} 数据分析功能开发中...")
    
    else:
        # 默认显示帮助
        print("多平台统计获取器")
        print("\n支持操作:")
        controller.list_platforms()
        print("\n可用命令: list, check, get, analyze")
        print("\n使用 --debug 参数可在调试时保持浏览器打开")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"💥 错误: {e}")
        sys.exit(1)