#!/usr/bin/env python3
"""
多平台统计数据获取工具 - 支持一键获取多个平台的统计数据
Multi-platform Statistics Acquisition Tool
参考 multi_platform_video_scheduler_final.py 架构
"""

import asyncio
import sys
import os
from pathlib import Path

# Windows系统编码处理
if sys.platform == 'win32': 
    os.system('chcp 65001')
    # 确保标准输出使用UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 工具类导入
from utils.multi_platform_ui import MultiPlatformUIManager
from utils.statistics_manager import StatisticsManager


class MultiStatsGetter:
    """多平台统计数据获取器"""
    
    def __init__(self):
        self.platforms = []
        self.operation_mode = "all"
        self.debug_mode = False
        self.generate_report = True
        self.results = {}
    
    def run(self):
        """运行完整的统计数据获取流程"""
        try:
            # 1. 打印标题
            MultiPlatformUIManager.print_stats_header()
            
            # 2. 选择平台
            self.platforms = MultiPlatformUIManager.select_platforms('stats')
            
            # 3. 选择操作模式
            self.operation_mode = MultiPlatformUIManager.select_operation_mode()
            
            # 4. 选择是否启用调试模式
            self.debug_mode = MultiPlatformUIManager.select_debug_mode()
            
            # 5. 选择是否生成报告
            self.generate_report = self._select_report_generation()
            
            # 6. 显示预览信息
            MultiPlatformUIManager.print_stats_preview(self.platforms)
            
            # 7. 用户确认
            if not MultiPlatformUIManager.get_user_confirmation():
                print("❌ 统计数据获取取消")
                return
            
            # 8. 执行统计数据获取
            asyncio.run(self._execute_stats_getting())
            
            # 9. 打印结果汇总
            StatisticsManager.print_statistics_summary(self.results)
            
            # 10. 生成报告
            if self.generate_report and any(self.results.values()):
                report_files = StatisticsManager.generate_statistics_report(self.results)
                print(f"\n📄 报告生成完成，共生成 {len(report_files)} 个文件")
            
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
        except Exception as e:
            print(f"\n💥 运行错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _select_report_generation(self) -> bool:
        """选择是否生成报告"""
        while True:
            try:
                choice = input("\n📄 是否生成统计报告? (Y/n, 默认Y): ").strip().lower()
                
                if not choice or choice in ['y', 'yes']:
                    print("✅ 将生成统计报告")
                    return True
                elif choice in ['n', 'no']:
                    print("✅ 跳过报告生成")
                    return False
                else:
                    print("❌ 请输入 Y 或 N")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    async def _execute_stats_getting(self):
        """执行统计数据获取操作"""
        print(f"\n🚀 开始执行统计数据获取...")
        print(f"📊 操作模式: {self.operation_mode}")
        print(f"🔍 调试模式: {'是' if self.debug_mode else '否'}")
        print(f"📄 报告生成: {'是' if self.generate_report else '否'}")
        
        if self.debug_mode:
            print("⚠️  调试模式下，每个平台都会保持浏览器打开状态")
            print("   请在每个平台的数据获取完成后手动关闭浏览器")
        
        if self.operation_mode == "all":
            # 批量获取所有
            await self._get_all_stats()
        elif self.operation_mode == "confirm":
            # 逐个确认获取
            await self._get_stats_with_confirmation()
        elif self.operation_mode == "missing":
            # 只获取有Cookie的平台
            await self._get_available_stats()
    
    async def _get_all_stats(self):
        """批量获取所有平台的统计数据"""
        total_platforms = len(self.platforms)
        
        for i, platform in enumerate(self.platforms, 1):
            MultiPlatformUIManager.print_progress(i, total_platforms, platform, "获取统计数据中...")
            
            try:
                data = await StatisticsManager.get_platform_statistics(platform, self.debug_mode)
                self.results[platform] = data
                
                if data is not None:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "✅ 成功")
                    
                    # 简要显示获取到的数据
                    followers = data.get('followers', 0)
                    following = data.get('following', 0)
                    likes = data.get('likes', 0)
                    videos = data.get('videos_count', 0)
                    
                    info = f"粉丝:{followers:,} 关注:{following:,} 获赞:{likes:,}"
                    if videos > 0:
                        info += f" 视频:{videos:,}"
                    print(f"   {'':21} {info}")
                else:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "❌ 失败")
                    
            except Exception as e:
                print(f"   {'':21} ❌ 获取 {platform} 统计数据时发生异常: {e}")
                self.results[platform] = None
                
                # 调试模式下提示用户检查
                if self.debug_mode:
                    print(f"   {'':21} 🔍 调试模式：请检查浏览器中的错误状态")
                    print(f"   {'':21}    按回车键继续下一个平台...")
                    try:
                        input()
                    except KeyboardInterrupt:
                        print(f"\n   {'':21} ⚠️  用户中断调试")
                        break
    
    async def _get_stats_with_confirmation(self):
        """逐个确认获取统计数据"""
        total_platforms = len(self.platforms)
        
        for i, platform in enumerate(self.platforms, 1):
            # 检查Cookie是否存在
            if not StatisticsManager.cookie_exists(platform):
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "❌ 缺少Cookie")
                self.results[platform] = None
                continue
            
            # 询问用户
            if MultiPlatformUIManager.confirm_platform_action(platform, '统计数据'):
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "获取统计数据中...")
                
            try:
                data = await StatisticsManager.get_platform_statistics(platform, self.debug_mode)
                self.results[platform] = data
                
                if data is not None:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "✅ 成功")
                    
                    # 简要显示获取到的数据
                    followers = data.get('followers', 0)
                    following = data.get('following', 0)
                    likes = data.get('likes', 0)
                    videos = data.get('videos_count', 0)
                    
                    info = f"粉丝:{followers:,} 关注:{following:,} 获赞:{likes:,}"
                    if videos > 0:
                        info += f" 视频:{videos:,}"
                    print(f"   {'':21} {info}")
                else:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "❌ 失败")
                    
            except Exception as e:
                print(f"   {'':21} ❌ 获取 {platform} 统计数据时发生异常: {e}")
                self.results[platform] = None
                
                # 调试模式下提示用户检查
                if self.debug_mode:
                    print(f"   {'':21} 🔍 调试模式：请检查浏览器中的错误状态")
                    print(f"   {'':21}    按回车键继续下一个平台...")
                    try:
                        input()
                    except KeyboardInterrupt:
                        print(f"\n   {'':21} ⚠️  用户中断调试")
                        break
            else:
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "⏭️  用户跳过")
                self.results[platform] = None
    
    async def _get_available_stats(self):
        """只获取有Cookie的平台统计数据"""
        total_platforms = len(self.platforms)
        available_platforms = []
        
        # 首先找出有Cookie的平台
        for platform in self.platforms:
            if StatisticsManager.cookie_exists(platform):
                available_platforms.append(platform)
        
        if not available_platforms:
            print("❌ 没有平台拥有有效的Cookie")
            print("   请先运行: python multi_get_cookies.py")
            for platform in self.platforms:
                self.results[platform] = None
            return
        
        print(f"📋 可获取统计数据的平台: {len(available_platforms)}/{total_platforms}")
        
        # 获取可用的统计数据
        for i, platform in enumerate(available_platforms, 1):
            MultiPlatformUIManager.print_progress(i, len(available_platforms), platform, "获取统计数据中...")
            
            data = await StatisticsManager.get_platform_statistics(platform, self.debug_mode)
            self.results[platform] = data
            
            if data is not None:
                MultiPlatformUIManager.print_progress(i, len(available_platforms), platform, "✅ 成功")
                
                # 简要显示获取到的数据
                followers = data.get('followers', 0)
                following = data.get('following', 0)
                likes = data.get('likes', 0)
                videos = data.get('videos_count', 0)
                
                info = f"粉丝:{followers:,} 关注:{following:,} 获赞:{likes:,}"
                if videos > 0:
                    info += f" 视频:{videos:,}"
                print(f"   {'':21} {info}")
            else:
                MultiPlatformUIManager.print_progress(i, len(available_platforms), platform, "❌ 失败")
        
        # 为没有Cookie的平台设置None状态
        for platform in self.platforms:
            if platform not in available_platforms:
                self.results[platform] = None


def main():
    """主函数"""
    print("📊 启动多平台统计数据获取工具...")
    
    # 检查依赖
    try:
        import playwright
        print("✅ Playwright 已安装")
    except ImportError:
        print("❌ Playwright 未安装，请运行: pip install playwright")
        return
    
    try:
        from conf import LOCAL_CHROME_PATH
        if Path(LOCAL_CHROME_PATH).exists():
            print(f"✅ Chrome 路径配置正确: {LOCAL_CHROME_PATH}")
        else:
            print(f"⚠️  Chrome 路径不存在: {LOCAL_CHROME_PATH}")
            print("   请检查 conf.py 中的 LOCAL_CHROME_PATH 配置")
    except Exception as e:
        print(f"❌ 配置文件错误: {e}")
        return
    
    # 检查统计模块
    try:
        from statistics.tencent_stat import get_tencent_statistics
        print("✅ 腾讯视频号统计模块已就绪")
    except ImportError:
        print("⚠️  腾讯视频号统计模块未找到，部分功能可能不可用")
    
    try:
        from statistics.kuaishou_stat import get_kuaishou_statistics
        print("✅ 快手统计模块已就绪")
    except ImportError:
        print("⚠️  快手统计模块未找到，部分功能可能不可用")
    
    # 运行主程序
    getter = MultiStatsGetter()
    getter.run()


if __name__ == "__main__":
    main()