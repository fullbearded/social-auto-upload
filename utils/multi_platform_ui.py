#!/usr/bin/env python3
"""
UI管理器 - 处理多平台Cookie和统计的用户交互
UI Manager - Handles user interaction for multi-platform cookies and statistics
"""

import sys
from typing import List, Dict, Optional
from utils.cookie_manager import CookieManager
from utils.statistics_manager import StatisticsManager


class MultiPlatformUIManager:
    """多平台UI管理器类"""
    
    @staticmethod
    def print_cookie_header():
        """打印Cookie获取标题"""
        print("=" * 60)
        print("🚀 多平台Cookie获取工具")
        print("支持平台: 抖音/小红书/快手/腾讯/哔哩哔哩/百家号/TikTok")
        print("=" * 60)
    
    @staticmethod
    def print_stats_header():
        """打印统计获取标题"""
        print("=" * 60)
        print("📊 多平台统计数据获取工具")
        print("支持平台: 快手/腾讯视频号")
        print("=" * 60)
    
    @staticmethod
    def select_platforms(manager_type: str = 'cookie') -> List[str]:
        """
        选择要操作的平台
        
        Args:
            manager_type: 'cookie' 或 'stats'
        """
        if manager_type == 'cookie':
            available_platforms = CookieManager.get_all_platforms()
            platform_notes = CookieManager.get_platform_notes()
        else:
            available_platforms = StatisticsManager.get_all_platforms()
            platform_notes = StatisticsManager.get_platform_notes()
        
        platform_list = list(available_platforms.items())
        
        print(f"\n📱 请选择要获取{'Cookie' if manager_type == 'cookie' else '统计数据'}的平台:")
        print("   (输入平台编号，多个平台用逗号分隔)")
        print("")
        
        for i, (key, name) in enumerate(platform_list, 1):
            note = platform_notes.get(key, '')
            status = ""
            
            if manager_type == 'cookie':
                status = f" - {CookieManager.get_cookie_status(key)}"
            else:
                status = f" - {StatisticsManager.get_platform_status(key)}"
            
            note_str = f" - {note}" if note else ""
            print(f"  {i}. {name} ({key}){status}{note_str}")
        
        print(f"\n💡 示例输入: 1,2,3  (表示选择前3个平台)")
        
        if manager_type == 'cookie':
            print("   直接按回车使用默认配置: 腾讯视频号")
            default_platforms = ['tencent']
        else:
            print("   直接按回车使用默认配置: 腾讯视频号,快手")
            default_platforms = ['tencent', 'ks']
        
        while True:
            try:
                user_input = input("\n🔧 请选择: ").strip()
                
                if not user_input:
                    print(f"✅ 使用默认配置: {', '.join([available_platforms.get(p, p) for p in default_platforms])}")
                    return default_platforms
                
                # 解析用户输入
                indices = [int(x.strip()) for x in user_input.split(',')]
                
                # 验证输入
                if all(1 <= idx <= len(platform_list) for idx in indices):
                    selected_platforms = [platform_list[idx - 1][0] for idx in indices]
                    print(f"✅ 已选择: {', '.join([available_platforms.get(p, p) for p in selected_platforms])}")
                    return selected_platforms
                else:
                    print(f"❌ 输入错误，请输入1-{len(platform_list)}之间的数字")
                    
            except ValueError:
                print("❌ 输入格式错误，请输入数字编号")
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    @staticmethod
    def select_operation_mode() -> str:
        """选择操作模式"""
        print("\n🔄 请选择操作模式:")
        print("  1. 获取所有选中平台的Cookie/统计数据")
        print("  2. 逐个确认获取Cookie/统计数据")
        print("  3. 只获取缺失的Cookie/统计数据")
        
        while True:
            try:
                choice = input("\n🔧 请选择模式 (1-3, 默认1): ").strip()
                
                if not choice:
                    choice = "1"
                
                if choice in ["1", "2", "3"]:
                    mode_map = {"1": "all", "2": "confirm", "3": "missing"}
                    selected_mode = mode_map[choice]
                    
                    mode_descriptions = {
                        "all": "批量获取所有选中平台",
                        "confirm": "逐个确认获取",
                        "missing": "只获取缺失的"
                    }
                    
                    print(f"✅ 已选择: {mode_descriptions[selected_mode]}")
                    return selected_mode
                else:
                    print("❌ 请输入1-3之间的数字")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    @staticmethod
    def confirm_platform_action(platform: str, action: str) -> bool:
        """确认是否对特定平台执行操作"""
        if action == 'cookie':
            platform_name = CookieManager.PlatformNames.get(platform, platform)
            exists = CookieManager.cookie_exists(platform)
        else:
            platform_name = StatisticsManager.PlatformNames.get(platform, platform)
            exists = StatisticsManager.cookie_exists(platform)
        
        if exists:
            status = "已存在" if action == 'cookie' else "Cookie已存在"
            print(f"\n📱 {platform_name} ({platform}) - {status}")
        else:
            status = "未获取" if action == 'cookie' else "Cookie缺失"
            print(f"\n📱 {platform_name} ({platform}) - {status}")
        
        while True:
            try:
                choice = input(f"   是否获取{action}? (Y/n, 默认Y): ").strip().lower()
                
                if not choice or choice in ['y', 'yes']:
                    return True
                elif choice in ['n', 'no']:
                    print(f"   ⏭️  跳过 {platform_name}")
                    return False
                else:
                    print("   ❌ 请输入 Y 或 N")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    @staticmethod
    def select_debug_mode() -> bool:
        """是否启用调试模式"""
        while True:
            try:
                choice = input("\n🔍 是否启用调试模式? (y/N, 默认N): ").strip().lower()
                
                if not choice or choice in ['n', 'no']:
                    print("✅ 使用正常模式")
                    return False
                elif choice in ['y', 'yes']:
                    print("✅ 启用调试模式")
                    print("   📝 调试模式下浏览器将保持打开状态")
                    return True
                else:
                    print("❌ 请输入 Y 或 N")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    @staticmethod
    def select_force_refresh() -> bool:
        """是否强制刷新"""
        while True:
            try:
                choice = input("\n🔄 是否强制重新获取已存在的Cookie? (y/N, 默认N): ").strip().lower()
                
                if not choice or choice in ['n', 'no']:
                    print("✅ 跳过已存在的Cookie")
                    return False
                elif choice in ['y', 'yes']:
                    print("✅ 将强制重新获取所有Cookie")
                    return True
                else:
                    print("❌ 请输入 Y 或 N")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)
    
    @staticmethod
    def print_progress(current: int, total: int, platform: str, status: str = "处理中"):
        """打印进度信息"""
        platform_name = CookieManager.PlatformNames.get(platform, platform)
        if platform_name == platform:  # 如果Cookie管理器中没有，尝试统计管理器
            platform_name = StatisticsManager.PlatformNames.get(platform, platform)
        
        progress = f"[{current}/{total}]"
        print(f"{progress} {platform_name:12} - {status}")
    
    @staticmethod
    def print_cookie_preview(platforms: List[str]):
        """打印Cookie预览信息"""
        print(f"\n📋 Cookie获取预览:")
        print("-" * 50)
        
        for platform in platforms:
            platform_name = CookieManager.PlatformNames.get(platform, platform)
            cookie_path = CookieManager.get_cookie_path(platform)
            status = CookieManager.get_cookie_status(platform)
            
            print(f"   {platform_name:10} ({platform:8}) - {status}")
            print(f"   路径: {cookie_path}")
    
    @staticmethod
    def print_stats_preview(platforms: List[str]):
        """打印统计预览信息"""
        print(f"\n📋 统计数据获取预览:")
        print("-" * 50)
        
        for platform in platforms:
            platform_name = StatisticsManager.PlatformNames.get(platform, platform)
            status = StatisticsManager.get_platform_status(platform)
            cookie_path = StatisticsManager.get_cookie_path(platform)
            
            print(f"   {platform_name:10} ({platform:8}) - {status}")
            print(f"   Cookie路径: {cookie_path}")
    
    @staticmethod
    def get_user_confirmation() -> bool:
        """获取用户最终确认"""
        print(f"\n{'='*50}")
        print("⚠️  请确认配置信息")
        print(f"{'='*50}")
        
        while True:
            try:
                choice = input("\n🚀 开始执行? (Y/n, 默认Y): ").strip().lower()
                
                if not choice or choice in ['y', 'yes']:
                    print("✅ 开始执行...")
                    return True
                elif choice in ['n', 'no']:
                    print("❌ 操作取消")
                    return False
                else:
                    print("❌ 请输入 Y 或 N")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消")
                sys.exit(0)