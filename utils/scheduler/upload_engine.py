#!/usr/bin/env python3
"""
上传引擎 - 处理视频上传的核心逻辑
Upload Engine - Core upload logic handler
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from utils.files_times import get_title_and_hashtags
from utils.scheduler.platform_manager import PlatformManager


class UploadEngine:
    """上传引擎类"""
    
    def __init__(self, platform: str, risk_controller=None):
        self.platform = platform
        self.risk_controller = risk_controller
        self.uploader_class = PlatformManager.get_uploader_class(platform)
        self.cookie_path = PlatformManager.get_cookie_path(platform)
    
    async def setup_platform_cookies(self, handle=False):
        """设置平台cookie
        
        Args:
            handle: 是否处理特殊情况
            
        Returns:
            bool: 设置是否成功
        """
        setup_func = PlatformManager.get_setup_function(self.platform)
        
        if not setup_func:
            if self.platform == 'bilibili':
                # Bilibili没有setup函数，检查cookie文件是否存在
                return self.cookie_path and self.cookie_path.exists()
            else:
                print(f"⚠️  平台 {self.platform} 未找到setup函数，跳过cookie验证")
                return True
        
        try:
            if self.platform == 'bilibili':
                return self.cookie_path and self.cookie_path.exists()
            
            return await setup_func(self.cookie_path, handle=handle)
        except Exception as e:
            print(f"❌ {self.platform} Cookie设置错误: {e}")
            return False
    
    def get_thumbnail_path(self, video_file: Path) -> Optional[Path]:
        """获取缩略图路径 - 支持多种格式"""
        # 尝试多种封面图格式
        possible_extensions = ['.png', '.jpg', '.jpeg']
        
        for ext in possible_extensions:
            thumbnail_path = video_file.with_suffix(ext)
            if thumbnail_path.exists():
                return thumbnail_path
        
        return None
    
    def format_upload_info(self, video_file: Path, title: str, tags: str, 
                          publish_time: datetime, video_info: Dict) -> Dict:
        """格式化上传信息"""
        time_str = publish_time.strftime('%Y-%m-%d %H:%M')
        remainder_flag = " (余数)" if video_info.get('is_remainder') else ""
        group_info = f" (第{video_info.get('group_id', 0)}组)" if video_info.get('group_id') else ""
        
        base_hour = video_info.get('base_hour', int(time_str.split(' ')[1].split(':')[0]))
        actual_minute = int(time_str.split(' ')[1].split(':')[1])
        time_offset_info = f" (+{actual_minute}分钟)" if actual_minute > 0 else ""
        
        return {
            'video_name': video_file.name,
            'title': title,
            'tags': tags,
            'time_str': time_str,
            'time_offset_info': time_offset_info,
            'remainder_flag': remainder_flag,
            'group_info': group_info
        }
    
    async def upload_video(self, video_file: Path, title: str, tags: str, 
                          publish_time: datetime, video_info: Dict, thumbnail_path: str = None) -> bool:
        """上传单个视频
        
        Args:
            video_file: 视频文件路径
            title: 视频标题
            tags: 视频标签
            publish_time: 发布时间
            video_info: 视频信息字典
            
        Returns:
            bool: 上传是否成功
        """
        if not self.uploader_class or not self.cookie_path:
            print(f"❌ 不支持的平台: {self.platform}")
            return False
        
        # 打印上传信息
        info = self.format_upload_info(video_file, title, tags, publish_time, video_info)
        print(f"\n📤 上传视频: {info['video_name']}")
        print(f"   标题: {info['title']}")
        print(f"   标签: {info['tags']}")
        print(f"   时间: {info['time_str']}{info['time_offset_info']}{info['remainder_flag']}{info['group_info']}")
        
        try:
            # 腾讯平台特殊处理
            if self.platform == 'tencent' and self.risk_controller:
                return await self._upload_tencent_video(
                    video_file, title, tags, publish_time, video_info, thumbnail_path
                )
            else:
                # 非腾讯平台，使用原始逻辑
                return await self._upload_general_video(
                    video_file, title, tags, publish_time, thumbnail_path
                )
        
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            
            # 记录失败信息给风控分析
            if self.risk_controller:
                self.risk_controller.record_upload_attempt(False, str(e))
                
            return False
    
    async def _upload_tencent_video(self, video_file: Path, title: str, tags: str,
                                  publish_time: datetime, video_info: Dict, thumbnail_path: str = None) -> bool:
        """腾讯平台上传处理"""
        from utils.tencent_risk_control import safe_tencent_upload
        
        print(f"🛡️  启用腾讯风控保护")
        print(f"   账号类型: {self.risk_controller.account_type}")
        print(f"   今日已上传: {self.risk_controller.day_count}")
        
        # 检查是否需要延迟
        if self.risk_controller.should_delay_upload():
            next_time = self.risk_controller.get_next_available_time()
            wait_seconds = (next_time - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                wait_minutes = int(wait_seconds // 60)
                print(f"⏳ 风控延迟: 需要等待 {wait_minutes} 分钟")
                
                # 询问用户是否继续等待
                try:
                    continue_upload = input(f"   🚦 是否等待 {wait_minutes} 分钟后继续？ (y/N): ").strip().lower()
                    if continue_upload != 'y':
                        return False
                except:
                    pass  # 非交互环境默认等待
                
                await asyncio.sleep(wait_seconds)
        
        # 使用传入的封面图路径，如果没有则自动生成
        if not thumbnail_path:
            thumbnail_path = self.get_thumbnail_path(video_file)
        
        if thumbnail_path:
            app = self.uploader_class(
                title, str(video_file), tags, publish_time, str(self.cookie_path), 
                thumbnail_path=str(thumbnail_path)
            )
        else:
            app = self.uploader_class(
                title, str(video_file), tags, publish_time, str(self.cookie_path)
            )
        
        # 使用风控保护的包装器执行上传
        async def upload_func():
            await app.main()
        
        return await safe_tencent_upload(upload_func, self.risk_controller)
    
    async def _upload_general_video(self, video_file: Path, title: str, tags: str,
                                  publish_time: datetime, thumbnail_path: str = None) -> bool:
        """通用平台上传处理"""
        # 使用传入的封面图路径，如果没有则自动生成
        if not thumbnail_path:
            thumbnail_path = self.get_thumbnail_path(video_file)
        
        if thumbnail_path:
            app = self.uploader_class(
                title, str(video_file), tags, publish_time, str(self.cookie_path), 
                thumbnail_path=str(thumbnail_path)
            )
        else:
            app = self.uploader_class(
                title, str(video_file), tags, publish_time, str(self.cookie_path)
            )
        
        await app.main()
        return True
    
    @classmethod
    async def upload_video_to_platform(cls, platform: str, video_file: Path, 
                                     title: str, tags: str, publish_time: datetime,
                                     video_info: Dict, risk_controller=None) -> bool:
        """静态方法：上传视频到指定平台
        
        Args:
            platform: 平台名称
            video_file: 视频文件路径
            title: 视频标题
            tags: 视频标签
            publish_time: 发布时间
            video_info: 视频信息
            risk_controller: 风控控制器（可选）
            
        Returns:
            bool: 上传是否成功
        """
        engine = cls(platform, risk_controller)
        # 从 video_info 中提取封面图路径
        thumbnail_path = video_info.get('thumbnail_path')
        return await engine.upload_video(video_file, title, tags, publish_time, video_info, thumbnail_path)