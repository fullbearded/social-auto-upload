#!/usr/bin/env python3
"""
多平台Cookie获取工具 - 支持一键获取多个平台的登录Cookie
Multi-platform Cookie Acquisition Tool
参考 multi_platform_video_scheduler_final.py 架构
"""

import asyncio
import sys
import os
from pathlib import Path

# Windows系统编码处理
if sys.platform == 'win32': 
    os.system('chcp 65001')

# 工具类导入
from utils.multi_platform_ui import MultiPlatformUIManager
from utils.cookie_manager import CookieManager


class MultiCookieGetter:
    """多平台Cookie获取器"""
    
    def __init__(self):
        self.platforms = []
        self.operation_mode = "all"
        self.force_refresh = False
        self.results = {}
    
    def run(self):
        """运行完整的Cookie获取流程"""
        try:
            # 1. 打印标题
            MultiPlatformUIManager.print_cookie_header()
            
            # 2. 验证和创建目录
            CookieManager.validate_cookie_directories()
            print("✅ Cookie目录验证完成")
            
            # 3. 选择平台
            self.platforms = MultiPlatformUIManager.select_platforms('cookie')
            
            # 4. 选择操作模式
            self.operation_mode = MultiPlatformUIManager.select_operation_mode()
            
            # 5. 选择是否强制刷新
            if self.operation_mode != "missing":
                self.force_refresh = MultiPlatformUIManager.select_force_refresh()
            
            # 6. 显示预览信息
            MultiPlatformUIManager.print_cookie_preview(self.platforms)
            
            # 7. 用户确认
            if not MultiPlatformUIManager.get_user_confirmation():
                print("❌ Cookie获取取消")
                return
            
            # 8. 执行Cookie获取
            asyncio.run(self._execute_cookie_getting())
            
            # 9. 打印结果汇总
            CookieManager.print_cookie_summary(self.results)
            
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
        except Exception as e:
            print(f"\n💥 运行错误: {e}")
            import traceback
            traceback.print_exc()
    
    async def _execute_cookie_getting(self):
        """执行Cookie获取操作"""
        print(f"\n🚀 开始执行Cookie获取...")
        print(f"📊 操作模式: {self.operation_mode}")
        print(f"🔄 强制刷新: {'是' if self.force_refresh else '否'}")
        
        if self.operation_mode == "all":
            # 批量获取所有
            await self._get_all_cookies()
        elif self.operation_mode == "confirm":
            # 逐个确认获取
            await self._get_cookies_with_confirmation()
        elif self.operation_mode == "missing":
            # 只获取缺失的
            await self._get_missing_cookies()
    
    async def _get_all_cookies(self):
        """批量获取所有平台的Cookie"""
        total_platforms = len(self.platforms)
        
        for i, platform in enumerate(self.platforms, 1):
            MultiPlatformUIManager.print_progress(i, total_platforms, platform, "获取Cookie中...")
            
            success = await CookieManager.get_platform_cookie(platform, self.force_refresh)
            self.results[platform] = success
            
            if success:
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "✅ 成功")
            else:
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "❌ 失败")
    
    async def _get_cookies_with_confirmation(self):
        """逐个确认获取Cookie"""
        total_platforms = len(self.platforms)
        
        for i, platform in enumerate(self.platforms, 1):
            # 检查是否需要获取
            if not self.force_refresh and CookieManager.cookie_exists(platform):
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "⏭️  已存在，跳过")
                self.results[platform] = True
                continue
            
            # 询问用户
            if MultiPlatformUIManager.confirm_platform_action(platform, 'cookie'):
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "获取Cookie中...")
                
                success = await CookieManager.get_platform_cookie(platform, self.force_refresh)
                self.results[platform] = success
                
                if success:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "✅ 成功")
                else:
                    MultiPlatformUIManager.print_progress(i, total_platforms, platform, "❌ 失败")
            else:
                MultiPlatformUIManager.print_progress(i, total_platforms, platform, "⏭️  用户跳过")
                self.results[platform] = False
    
    async def _get_missing_cookies(self):
        """只获取缺失的Cookie"""
        total_platforms = len(self.platforms)
        missing_platforms = []
        
        # 首先找出缺失的平台
        for platform in self.platforms:
            if not CookieManager.cookie_exists(platform):
                missing_platforms.append(platform)
        
        if not missing_platforms:
            print("✅ 所有平台Cookie都已存在，无需获取")
            for platform in self.platforms:
                self.results[platform] = True
            return
        
        print(f"📋 需要获取Cookie的平台: {len(missing_platforms)}/{total_platforms}")
        
        # 获取缺失的Cookie
        for i, platform in enumerate(missing_platforms, 1):
            MultiPlatformUIManager.print_progress(i, len(missing_platforms), platform, "获取Cookie中...")
            
            success = await CookieManager.get_platform_cookie(platform, False)
            self.results[platform] = success
            
            if success:
                MultiPlatformUIManager.print_progress(i, len(missing_platforms), platform, "✅ 成功")
            else:
                MultiPlatformUIManager.print_progress(i, len(missing_platforms), platform, "❌ 失败")
        
        # 为已存在的平台设置成功状态
        for platform in self.platforms:
            if platform not in missing_platforms:
                self.results[platform] = True


def main():
    """主函数"""
    print("🚀 启动多平台Cookie获取工具...")
    
    # 检查依赖
    try:
        import patchright
        print("✅ Patchright 已安装")
    except ImportError:
        print("❌ Patchright 未安装，请运行: uv sync")
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
    
    # 运行主程序
    getter = MultiCookieGetter()
    getter.run()


if __name__ == "__main__":
    main()