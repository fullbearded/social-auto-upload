#!/usr/bin/env python3
"""
配置管理器 - 处理配置参数和常量
Config Manager - Handles configuration parameters and constants
"""

from typing import List, Dict, Optional


class ConfigManager:
    """配置管理器类"""
    
    # 默认发布时间点
    DEFAULT_PUBLISH_TIMES = [5, 8, 12, 17, 19]  # 6:00, 11:00, 15:00等
    
    # 默认分组大小
    DEFAULT_GROUP_SIZE = 5
    
    # 默认开始天数（从明天开始）
    DEFAULT_START_DAYS = 0
    
    # 默认随机偏移时间（分钟）
    DEFAULT_RANDOM_MINUTES = 10
    
    # 风险控制的默认参数
    TENGUIN_ACCOUNT_TYPES = {
        "new": {
            "max_daily_uploads": 3,
            "min_interval_minutes": 30,
            "max_interval_minutes": 120,
            "description": "新账号 (≤2周，≤10次上传)"
        },
        "standard": {
            "max_daily_uploads": 10,
            "min_interval_minutes": 15,
            "max_interval_minutes": 90,
            "description": "标准账号 (≤2个月，≤100次上传)"
        },
        "mature": {
            "max_daily_uploads": 20,
            "min_interval_minutes": 10,
            "max_interval_minutes": 60,
            "description": "成熟账号 (>2个月，>100次上传)"
        }
    }
    
    # 快手特殊配置
    KUAISHOU_CONFIG = {
        "min_delay_seconds": 60,
        "max_delay_seconds": 300,
        "description": "快手上传间隔保护"
    }
    
    @classmethod
    def get_default_publish_times(cls) -> List[int]:
        """获取默认发布时间"""
        return cls.DEFAULT_PUBLISH_TIMES.copy()
    
    @classmethod
    def get_default_group_size(cls) -> int:
        """获取默认分组大小"""
        return cls.DEFAULT_GROUP_SIZE
    
    @classmethod
    def get_default_start_days(cls) -> int:
        """获取默认开始天数"""
        return cls.DEFAULT_START_DAYS
    
    @classmethod
    def get_default_random_minutes(cls) -> int:
        """获取默认随机偏移分钟数"""
        return cls.DEFAULT_RANDOM_MINUTES
    
    @classmethod
    def get_tencuin_account_config(cls, account_type: str) -> Dict:
        """获取腾讯账号配置"""
        return cls.TENGUIN_ACCOUNT_TYPES.get(account_type, cls.TENGUIN_ACCOUNT_TYPES["standard"])
    
    @classmethod
    def get_kuaishou_config(cls) -> Dict:
        """获取快手配置"""
        return cls.KUAISHOU_CONFIG.copy()
    
    @classmethod
    def create_scheduler_config(cls, custom_config: Optional[Dict] = None) -> Dict:
        """
        创建调度配置
        
        Args:
            custom_config: 自定义配置
            
        Returns:
            Dict: 完整的配置字典
        """
        config = {
            'publish_times': cls.DEFAULT_PUBLISH_TIMES,
            'group_size': cls.DEFAULT_GROUP_SIZE,
            'start_days': cls.DEFAULT_START_DAYS,
            'random_minutes': cls.DEFAULT_RANDOM_MINUTES,
            'tencuin_account_type': 'standard',
            'kuaishou_delay_range': [cls.KUAISHOU_CONFIG['min_delay_seconds'], 
                                   cls.KUAISHOU_CONFIG['max_delay_seconds']]
        }
        
        if custom_config:
            config.update(custom_config)
        
        return config
    
    @classmethod
    def validate_config(cls, config: Dict) -> bool:
        """
        验证配置有效性
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
        """
        required_keys = ['publish_times', 'group_size', 'start_days']
        
        for key in required_keys:
            if key not in config:
                print(f"❌ 配置缺少必要参数: {key}")
                return False
        
        # 验证发布时间点
        if not isinstance(config['publish_times'], list):
            print("❌ publish_times必须是列表")
            return False
        
        if not all(isinstance(t, int) and 0 <= t < 24 for t in config['publish_times']):
            print("❌ publish_times必须是0-23范围内的整数")
            return False
        
        # 验证分组大小
        if not isinstance(config['group_size'], int) or config['group_size'] <= 0:
            print("❌ group_size必须是正整数")
            return False
        
        # 验证开始天数
        if not isinstance(config['start_days'], int) or config['start_days'] < 0:
            print("❌ start_days必须是非负整数")
            return False
        
        # 验证随机偏移
        random_minutes = config.get('random_minutes', cls.DEFAULT_RANDOM_MINUTES)
        if not isinstance(random_minutes, int) or random_minutes < 0:
            print("❌ random_minutes必须是非负整数")
            return False
        
        # 验证腾讯账号类型
        tencuin_type = config.get('tencuin_account_type', 'standard')
        if tencuin_type not in cls.TENGUIN_ACCOUNT_TYPES:
            print(f"❌ 无效的腾讯账号类型: {tencuin_type}")
            return False
        
        return True
    
    @classmethod
    def create_risk_controller_config(cls, account_type: str) -> Dict:
        """
        创建风控控制器配置
        
        Args:
            account_type: 账号类型
            
        Returns:
            Dict: 风控配置
        """
        account_config = cls.get_tencuin_account_config(account_type)
        
        return {
            'account_type': account_type,
            'max_daily_uploads': account_config['max_daily_uploads'],
            'min_interval_minutes': account_config['min_interval_minutes'],
            'max_interval_minutes': account_config['max_interval_minutes'],
            'description': account_config['description']
        }