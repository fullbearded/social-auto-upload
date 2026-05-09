#!/usr/bin/env python3
"""
Cookie管理器 - 处理多平台Cookie获取和管理
Cookie Manager - Handles multi-platform cookie acquisition and management
"""

import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type
from conf import BASE_DIR


class CookieManager:
    """Cookie管理器类"""
    
    # 平台Cookie获取函数映射
    CookieMapping = {
        'douyin': 'uploader.douyin_uploader.main.douyin_setup',
        'xiaohongshu': 'uploader.xiaohongshu_uploader.main.xiaohongshu_setup',
        'xhs': 'uploader.xiaohongshu_uploader.main.xiaohongshu_setup',
        'kuaishou': 'uploader.ks_uploader.main.ks_setup',
        'tencent': 'uploader.tencent_uploader.main.weixin_setup',
        'bilibili': 'uploader.bilibili_uploader.main.bilibili_setup',
        'baijiahao': 'uploader.baijiahao_uploader.main.baijiahao_setup',
        'tk': 'uploader.tk_uploader.main.tk_setup',
    }
    
    # 平台Cookie文件路径映射
    CookiePathMapping = {
        'douyin': 'cookies/douyin_uploader/account.json',
        'xiaohongshu': 'cookies/xiaohongshu_uploader/account.json',
        'xhs': 'cookies/xiaohongshu_uploader/account.json',
        'kuaishou': 'cookies/ks_uploader/account.json',
        'ks': 'cookies/ks_uploader/account.json',
        'tencent': 'cookies/tencent_uploader/account.json',
        'bilibili': 'cookies/bilibili_uploader/account.json',
        'baijiahao': 'cookies/baijiahao_uploader/account.json',
        'tk': 'cookies/tk_uploader/account.json',
    }
    
    # 平台显示名称
    PlatformNames = {
        'douyin': '抖音',
        'xiaohongshu': '小红书',
        'xhs': '小红书',
        'kuaishou': '快手',
        'tencent': '腾讯视频号',
        'bilibili': '哔哩哔哩',
        'baijiahao': '百家号',
        'tk': 'TikTok',
    }
    
    # 平台描述和注意事项
    PlatformNotes = {
        'douyin': '需要手机号登录',
        'xiaohongshu': '需要微信登录',
        'kuaishou': '需要快手账号登录',
        'tencent': '需要微信扫码登录',
        'bilibili': '需要哔哩哔哩账号登录',
        'baijiahao': '需要百度账号登录',
        'tk': '需要TikTok账号（需要特殊网络）',
    }
    
    @classmethod
    def get_all_platforms(cls) -> Dict[str, str]:
        """获取所有支持的平台"""
        return cls.PlatformNames.copy()
    
    @classmethod
    def get_platform_notes(cls) -> Dict[str, str]:
        """获取平台注意事项"""
        return cls.PlatformNotes.copy()
    
    @classmethod
    def get_cookie_path(cls, platform: str) -> Path:
        """获取平台Cookie文件路径"""
        if platform in cls.CookiePathMapping:
            return BASE_DIR / cls.CookiePathMapping[platform]
        return BASE_DIR / f"cookies/{platform}_uploader/account.json"
    
    @classmethod
    def cookie_exists(cls, platform: str) -> bool:
        """检查Cookie文件是否存在"""
        cookie_path = cls.get_cookie_path(platform)
        return cookie_path.exists()
    
    @classmethod
    def get_cookie_status(cls, platform: str) -> str:
        """获取Cookie状态"""
        if cls.cookie_exists(platform):
            return "✅ 已存在"
        else:
            return "❌ 未获取"
    
    @classmethod
    async def get_platform_cookie(cls, platform: str, force_refresh: bool = False) -> bool:
        """
        获取指定平台的Cookie
        
        Args:
            platform: 平台名称
            force_refresh: 是否强制重新获取
        
        Returns:
            是否成功获取Cookie
        """
        if not force_refresh and cls.cookie_exists(platform):
            print(f"⚠️  {cls.PlatformNames.get(platform, platform)} Cookie已存在，跳过获取")
            return True
        
        if platform not in cls.CookieMapping:
            print(f"❌ 平台 {platform} 不支持Cookie获取")
            return False
        
        try:
            # 动态导入获取函数
            module_path, function_name = cls.CookieMapping[platform].rsplit('.', 1)
            module = importlib.import_module(module_path)
            get_cookie_func = getattr(module, function_name)
            
            cookie_path = cls.get_cookie_path(platform)
            
            print(f"🔄 正在获取 {cls.PlatformNames.get(platform, platform)} Cookie...")
            print(f"📝 Cookie将保存到: {cookie_path}")
            
            # 调用获取函数
            result = await get_cookie_func(str(cookie_path), handle=True)
            
            if result:
                print(f"✅ {cls.PlatformNames.get(platform, platform)} Cookie获取成功")
                return True
            else:
                print(f"❌ {cls.PlatformNames.get(platform, platform)} Cookie获取失败")
                return False
                
        except ImportError as e:
            print(f"❌ 无法导入 {platform} 的Cookie获取模块: {e}")
            return False
        except AttributeError as e:
            print(f"❌ {platform} 的Cookie获取函数不存在: {e}")
            return False
        except Exception as e:
            print(f"❌ 获取 {platform} Cookie时出错: {e}")
            return False
    
    @classmethod
    async def get_multiple_cookies(cls, platforms: List[str], force_refresh: bool = False) -> Dict[str, bool]:
        """
        批量获取多个平台的Cookie
        
        Args:
            platforms: 平台列表
            force_refresh: 是否强制重新获取
        
        Returns:
            各平台获取结果字典
        """
        results = {}
        
        print("🚀 开始批量获取Cookie...")
        print(f"📱 目标平台: {', '.join([cls.PlatformNames.get(p, p) for p in platforms])}")
        
        for i, platform in enumerate(platforms, 1):
            print(f"\n{'='*50}")
            print(f"📊 进度: {i}/{len(platforms)} - {cls.PlatformNames.get(platform, platform)}")
            print(f"{'='*50}")
            
            success = await cls.get_platform_cookie(platform, force_refresh)
            results[platform] = success
        
        return results
    
    @classmethod
    def print_cookie_summary(cls, results: Dict[str, bool]):
        """打印Cookie获取结果汇总"""
        print(f"\n{'='*60}")
        print("📊 Cookie获取结果汇总")
        print(f"{'='*60}")
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            platform_name = cls.PlatformNames.get(platform, platform)
            print(f"   {platform_name:10} ({platform:8}) - {status}")
        
        print(f"\n📈 总计: {success_count}/{total_count} 成功")
        
        if success_count == total_count:
            print("🎉 所有平台Cookie获取完成！")
        elif success_count == 0:
            print("💥 所有平台Cookie获取失败！")
        else:
            print("⚠️  部分平台Cookie获取失败，请检查错误信息")
    
    @classmethod
    def validate_cookie_directories(cls):
        """验证和创建Cookie目录"""
        for platform in cls.CookiePathMapping.keys():
            cookie_path = cls.get_cookie_path(platform)
            cookie_path.parent.mkdir(parents=True, exist_ok=True)