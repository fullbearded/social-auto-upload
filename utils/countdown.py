#!/usr/bin/env python3
"""
倒计时工具模块
提供命令行倒计时功能
"""

import asyncio
import sys
from datetime import datetime, timedelta


class CountdownTimer:
    """命令行倒计时器"""
    
    def __init__(self, total_seconds: int, prefix: str = "⏳ 等待"):
        self.total_seconds = total_seconds
        self.prefix = prefix
        self.start_time = None
        
    async def start(self):
        """开始倒计时"""
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(seconds=self.total_seconds)
        
        print(f"{self.prefix}{self.total_seconds}秒...")
        print("=" * 50)
        
        try:
            for remaining in range(self.total_seconds, 0, -1):
                # 计算进度条
                progress = (self.total_seconds - remaining) / self.total_seconds
                bar_length = 30
                filled_length = int(bar_length * progress)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # 格式化剩余时间
                minutes, seconds = divmod(remaining, 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
                
                # 输出倒计时信息
                sys.stdout.write(f"\r[{bar}] {time_str} | 进度: {progress*100:.1f}%")
                sys.stdout.flush()
                
                await asyncio.sleep(1)
                
            # 倒计时结束
            sys.stdout.write("\r" + " " * 80 + "\r")  # 清除行
            print(f"{self.prefix}完成 ✅")
            print("=" * 50)
            
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            print("⏸️  倒计时被中断")
            return False
            
        return True
    
    def get_remaining_time(self) -> int:
        """获取剩余时间（秒）"""
        if not self.start_time:
            return self.total_seconds
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = max(0, self.total_seconds - int(elapsed))
        return remaining


async def countdown_with_progress(total_seconds: int, prefix: str = "⏳ 等待"):
    """简单的倒计时函数
    
    Args:
        total_seconds: 总秒数
        prefix: 前缀文本
    
    Returns:
        bool: 是否完成倒计时
    """
    timer = CountdownTimer(total_seconds, prefix)
    return await timer.start()


async def countdown_for_platform(platform: str, seconds: int):
    """平台专用倒计时
    
    Args:
        platform: 平台名称
        seconds: 等待秒数
    """
    prefix = f"⏳ {platform.upper()} 平台间隔保护 - 等待"
    return await countdown_with_progress(seconds, prefix)