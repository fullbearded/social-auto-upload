#!/usr/bin/env python3
"""
平台管理器 - 处理平台相关的配置和映射
Platform Manager - Handles platform configurations and mappings
"""

from pathlib import Path
from typing import Dict, Optional, Type
from conf import BASE_DIR


class PlatformManager:
    """平台管理器类"""
    
    # 平台上传器映射
    UploaderMapping = {
        'douyin': 'uploader.douyin_uploader.main.DouYinVideo',
        'bilibili': 'uploader.bilibili_uploader.main.BilibiliUploader', 
        'xiaohongshu': 'uploader.xiaohongshu_uploader.main.XiaoHongShuVideo',
        'kuaishou': 'uploader.ks_uploader.main.KSVideo',
        'baijiahao': 'uploader.baijiahao_uploader.main.BaiJiaHaoVideo',
        'tencent': 'uploader.tencent_uploader.main.TencentVideo',
        'tk': 'uploader.tk_uploader.main.TiktokVideo',
        'ks': 'uploader.ks_uploader.main.KSVideo',
    }
    
    # 平台设置函数映射
    SetupMapping = {
        'douyin': 'uploader.douyin_uploader.main.douyin_setup',
        'xiaohongshu': 'uploader.xiaohongshu_uploader.main.xiaohongshu_setup',
        'kuaishou': 'uploader.ks_uploader.main.ks_setup',
        'baijiahao': 'uploader.baijiahao_uploader.main.baijiahao_setup',
        'tencent': 'uploader.tencent_uploader.main.weixin_setup',
        'tk': 'uploader.tk_uploader.main.tiktok_setup',
        'ks': 'uploader.ks_uploader.main.ks_setup',
    }
    
    # 平台显示名称映射
    DisplayNames = {
        'douyin': '抖音',
        'bilibili': '哔哩哔哩',
        'xiaohongshu': '小红书',
        'kuaishou': '快手',
        'baijiahao': '百家号',
        'tencent': '腾讯视频号',
        'tk': 'TikTok',
        'ks': '快手(备用)',
    }
    
    # 平台特殊说明
    PlatformNotes = {
        'douyin': '支持自定义封面，需要抖音创作者账号',
        'bilibili': '需要biliup库，支持视频分区选择',
        'xiaohongshu': '支持自定义封面和地理位置',
        'kuaishou': '限制最多3个话题标签',
        'baijiahao': '支持AI成片功能，需要百家号创作者权限',
        'tencent': '腾讯视频号，支持原创声明和商品添加 - ✅风控保护已启用',
        'tk': 'TikTok，使用Firefox浏览器（特殊）',
        'ks': '快手备用上传器，功能类似',
    }
    
    @classmethod
    def get_uploader_class(cls, platform: str):
        """获取对应平台的上传器类"""
        try:
            module_path = cls.UploaderMapping.get(platform)
            if not module_path:
                return None
            
            parts = module_path.split('.')
            module_name = '.'.join(parts[:-1])
            class_name = parts[-1]
            
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError, KeyError):
            return None
    
    @classmethod
    def get_setup_function(cls, platform: str):
        """获取对应平台的设置函数"""
        try:
            func_path = cls.SetupMapping.get(platform)
            if not func_path:
                return None
            
            parts = func_path.split('.')
            module_name = '.'.join(parts[:-1])
            func_name = parts[-1]
            
            module = __import__(module_name, fromlist=[func_name])
            return getattr(module, func_name)
        except (ImportError, AttributeError, KeyError):
            return None
    
    @classmethod
    def get_cookie_path(cls, platform: str) -> Optional[Path]:
        """获取对应平台的cookie文件路径"""
        cookie_paths = {
            'douyin': Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json",
            'bilibili': Path(BASE_DIR) / "cookies" / "bilibili_uploader" / "account.json",
            'xiaohongshu': Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json",
            'kuaishou': Path(BASE_DIR) / "cookies" / "ks_uploader" / "account.json",
            'baijiahao': Path(BASE_DIR) / "cookies" / "baijiahao_uploader" / "account.json",
            'tencent': Path(BASE_DIR) / "cookies" / "tencent_uploader" / "account.json",
            'tk': Path(BASE_DIR) / "cookies" / "tk_uploader" / "account.json",
            'ks': Path(BASE_DIR) / "cookies" / "ks_uploader" / "account.json",
        }
        return cookie_paths.get(platform)
    
    @classmethod
    def get_display_names(cls, platforms: list) -> Dict[str, str]:
        """获取平台的显示名称"""
        return {platform: cls.DisplayNames.get(platform, platform) 
                for platform in platforms}
    
    @classmethod
    def get_all_platforms(cls) -> Dict[str, str]:
        """获取所有可用平台"""
        return cls.DisplayNames.copy()
    
    @classmethod
    def get_platform_notes(cls, platform: str = None) -> Dict[str, str]:
        """获取平台特殊说明"""
        if platform:
            return {platform: cls.PlatformNotes.get(platform, '')}
        return cls.PlatformNotes.copy()
    
    @classmethod
    def is_valid_platform(cls, platform: str) -> bool:
        """检查是否为有效平台"""
        return platform in cls.DisplayNames
    
    @classmethod
    def get_available_platforms(cls) -> list:
        """获取可用平台列表"""
        return list(cls.DisplayNames.keys())