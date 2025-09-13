"""
腾讯视频号风控规避系统
Tencent WeChat Video Platform Risk Control Avoidance System

功能特点：
- 智能延迟算法：基于账号成熟度动态调整发布间隔
- 行为模式模拟：模拟真实用户的自然发布行为
- 风险监测：实时监控平台风控响应
- 频率限制：每小时/每日上传配额管理
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from pathlib import Path


class TencentRiskController:
    """腾讯风控控制器"""
    
    def __init__(self, account_type: str = "new", log_file: str = None):
        """
        初始化风控控制器
        
        Args:
            account_type: 账号类型 ["new", "standard", "mature"]
            log_file: 日志文件路径
        """
        self.account_type = account_type
        self.risk_log = []
        
        # 不同账号类型的限制配置
        self.limits = {
            "new": {
                "max_per_hour": 1,
                "max_per_day": 3,
                "min_delay_minutes": 25,
                "max_delay_minutes": 45,
                "daily_cooldown_hours": 6
            },
            "standard": {
                "max_per_hour": 2,
                "max_per_day": 8,
                "min_delay_minutes": 15,
                "max_delay_minutes": 30,
                "daily_cooldown_hours": 4
            },
            "mature": {
                "max_per_hour": 3,
                "max_per_day": 12,
                "min_delay_minutes": 8,
                "max_delay_minutes": 18,
                "daily_cooldown_hours": 2
            }
        }
        
        # 当前计数
        self.hour_count = 0
        self.day_count = 0
        self.upload_history = []
        
        # 设置日志
        self.logger = logging.getLogger('tencent_risk_control')
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def should_delay_upload(self, now: datetime = None) -> bool:
        """
        判断是否需要延迟上传
        
        Returns:
            bool: 是否需要延迟
        """
        if now is None:
            now = datetime.now()
            
        # 检查每小时限制
        current_hour = now.hour
        hour_uploads = [upload for upload in self.upload_history 
                       if upload['time'].hour == current_hour and 
                       upload['time'].date() == now.date()]
        
        if len(hour_uploads) >= self.limits[self.account_type]["max_per_hour"]:
            self.logger.warning(f"每小时限制: {len(hour_uploads)} >= {self.limits[self.account_type]['max_per_hour']}")
            return True
            
        # 检查每日限制
        day_uploads = [upload for upload in self.upload_history 
                      if upload['time'].date() == now.date()]
        
        if len(day_uploads) >= self.limits[self.account_type]["max_per_day"]:
            self.logger.warning(f"每日限制: {len(day_uploads)} >= {self.limits[self.account_type]['max_per_day']}")
            return True
            
        return False

    def calculate_smart_delay(self, last_upload_time: datetime = None) -> int:
        """
        计算智能延迟时间
        
        Args:
            last_upload_time: 上次上传时间
            
        Returns:
            int: 延迟时间（秒）
        """
        now = datetime.now()
        
        if last_upload_time is None:
            # 首次上传，使用最小延迟的一半作为安全延迟
            min_delay = self.limits[self.account_type]["min_delay_minutes"]
            return random.randint(min_delay * 30, min_delay * 60)
            
        # 基于账号类型的随机延迟
        min_delay = self.limits[self.account_type]["min_delay_minutes"] * 60
        max_delay = self.limits[self.account_type]["max_delay_minutes"] * 60
        
        # 添加随机因素模拟行为模式
        base_delay = random.randint(min_delay, max_delay)
        
        # 时间权重：下班时间（19-22点）更快，上班时间（9-18点）更慢
        current_hour = now.hour
        if 19 <= current_hour <= 22:
            base_delay = int(base_delay * 0.8)  # 下班时间更快
        elif 9 <= current_hour <= 18:
            base_delay = int(base_delay * 1.2)  # 上班时间更慢
            
        return base_delay

    def calculate_daily_cooldown(self) -> int:
        """
        计算每日冷却时间
        
        Returns:
            int: 冷却时间（秒）
        """
        cooldown_hours = self.limits[self.account_type]["daily_cooldown_hours"]
        return cooldown_hours * 3600 + random.randint(0, 1800)  # 添加0-30分钟的随机延迟

    def record_upload_attempt(self, success: bool, error_code: str = None, platform_response: str = None):
        """
        记录上传尝试
        
        Args:
            success: 是否成功
            error_code: 错误代码
            platform_response: 平台响应
        """
        record = {
            'time': datetime.now(),
            'success': success,
            'error_code': error_code,
            'platform_response': platform_response,
            'account_type': self.account_type
        }
        
        self.upload_history.append(record)
        self.logger.info(f"上传记录: {record}")
        
        # 检测到风控响应时的处理
        if error_code and "risk" in error_code.lower():
            self.logger.error(f"检测到风控: {error_code}")
            self.adjust_for_risk_detected()

    def adjust_for_risk_detected(self):
        """检测到风控时的策略调整"""
        # 增加延迟时间 50%
        limits = self.limits[self.account_type]
        limits["min_delay_minutes"] = int(limits["min_delay_minutes"] * 1.5)
        limits["max_delay_minutes"] = int(limits["max_delay_minutes"] * 1.5)
        limits["daily_cooldown_hours"] = int(limits["daily_cooldown_hours"] * 1.5)
        
        self.logger.warning(f"风控检测，调整延迟策略: {self.limits[self.account_type]}")

    def get_daily_stats(self, date: datetime.date = None) -> Dict:
        """
        获取每日统计
        
        Args:
            date: 指定日期，使用当天时不指定
            
        Returns:
            Dict: 统计信息
        """
        if date is None:
            date = datetime.now().date()
            
        day_uploads = [upload for upload in self.upload_history 
                      if upload['time'].date() == date]
        
        return {
            'total_attempts': len(day_uploads),
            'successful_uploads': len([u for u in day_uploads if u['success']]),
            'failed_uploads': len([u for u in day_uploads if not u['success']]),
            'risk_incidents': len([u for u in day_uploads 
                                 if u['error_code'] and 'risk' in str(u['error_code']).lower()])
        }

    def reset_daily_counters(self):
        """重置每日计数器"""
        self.hour_count = 0
        self.day_count = 0
        
    def get_next_available_time(self) -> datetime:
        """
        计算下次可上传时间
        
        Returns:
            datetime: 下次可上传时间
        """
        now = datetime.now()
        
        # 基于当前限制计算下次时间
        today_uploads = [upload for upload in self.upload_history 
                        if upload['time'].date() == now.date()]
        
        if len(today_uploads) >= self.limits[self.account_type]["max_per_day"]:
            # 次日0点后允许再次上传
            tomorrow = now.date() + timedelta(days=1)
            next_time = datetime.combine(tomorrow, datetime.min.time())
            
            # 添加随机延迟
            random_hours = random.randint(1, 6)
            random_minutes = random.randint(0, 59)
            next_time = next_time + timedelta(hours=random_hours, minutes=random_minutes)
            
        else:
            # 同日内，计算小时限制
            current_hour = now.hour
            hour_uploads = [upload for upload in self.upload_history 
                           if upload['time'].hour == current_hour and 
                           upload['time'].date() == now.date()]
            
            if len(hour_uploads) >= self.limits[self.account_type]["max_per_hour"]:
                # 下一个小时开始时可上传
                next_time = now.replace(hour=current_hour+1, minute=random.randint(0, 15), second=0)
            else:
                # 计算智能延迟后即可上传
                last_upload = max(today_uploads, key=lambda x: x['time']) if today_uploads else None
                delay = self.calculate_smart_delay(
                    last_upload['time'] if last_upload else None)
                next_time = now + timedelta(seconds=delay)
                
        return next_time


def detect_account_maturity(account_age_days: int, total_uploads: int) -> str:
    """
    基于账号使用情况检测成熟度
    
    Args:
        account_age_days: 账号使用天数
        total_uploads: 总上传次数
        
    Returns:
        str: 账号类型 ["new", "standard", "mature"]
    """
    if account_age_days < 14 or total_uploads < 10:
        return "new"
    elif account_age_days < 60 or total_uploads < 100:
        return "standard"
    else:
        return "mature"


async def safe_tencent_upload(upload_func, risk_controller: TencentRiskController, 
                             max_retries: int = 3) -> bool:
    """
    安全的腾讯上传包装器
    
    Args:
        upload_func: 上传函数
        risk_controller: 风控控制器
        max_retries: 最大重试次数
        
    Returns:
        bool: 是否成功
    """
    for attempt in range(max_retries):
        try:
            # 检查是否需要延迟
            if risk_controller.should_delay_upload():
                delay = risk_controller.calculate_smart_delay()
                logging.info(f"风控检测：延迟 {delay//60} 分钟后再试")
                await asyncio.sleep(delay)
                
            # 执行上传
            result = await upload_func()
            
            # 记录成功
            risk_controller.record_upload_attempt(True)
            return True
            
        except Exception as e:
            error_msg = str(e)
            risk_controller.record_upload_attempt(False, error_msg)
            
            if attempt < max_retries - 1:
                # 刷退策略：指数退避
                backoff_seconds = min(300, (2 ** attempt) * 60)
                logging.warning(f"上传重试 {attempt + 1}: 延迟 {backoff_seconds} 秒")
                await asyncio.sleep(backoff_seconds)
            else:
                logging.error(f"上传失败: {error_msg}")
                return False
                
    return False