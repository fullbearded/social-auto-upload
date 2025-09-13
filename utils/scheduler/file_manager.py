#!/usr/bin/env python3
"""
文件管理器 - 处理文件系统操作
File Manager - Handles file system operations
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from conf import BASE_DIR


class FileManager:
    """文件管理器类"""
    
    @staticmethod
    def get_videos_directory() -> Path:
        """获取视频目录路径"""
        return Path(BASE_DIR) / "videos"
    
    @staticmethod
    def get_logs_directory() -> Path:
        """获取日志目录路径"""
        logs_dir = Path(BASE_DIR) / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    @staticmethod
    def get_cookies_directory() -> Path:
        """获取Cookie目录路径"""
        return Path(BASE_DIR) / "cookies"
    
    @staticmethod
    def find_video_files(directory: Optional[Path] = None) -> List[Path]:
        """
        查找视频文件
        
        Args:
            directory: 目录路径（默认为videos目录）
            
        Returns:
            List[Path]: 视频文件路径列表
        """
        if directory is None:
            directory = FileManager.get_videos_directory()
        
        if not directory.exists():
            return []
        
        return list(directory.glob("*.mp4"))
    
    @staticmethod
    def validate_video_directory(directory: Optional[Path] = None) -> bool:
        """
        验证视频目录
        
        Args:
            directory: 目录路径（默认为videos目录）
            
        Returns:
            bool: 目录是否存在
        """
        if directory is None:
            directory = FileManager.get_videos_directory()
        
        if not directory.exists():
            print(f"❌ 视频目录不存在: {directory}")
            return False
        
        return True
    
    @staticmethod
    def get_kuaishou_upload_log_filename() -> Path:
        """获取快手上传日志文件名"""
        logs_dir = FileManager.get_logs_directory()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return logs_dir / f"kuaishou_upload_{timestamp}.log"
    
    @staticmethod
    def get_tencent_risk_log_filename(account_type: str) -> Path:
        """获取腾讯风控日志文件名"""
        logs_dir = FileManager.get_logs_directory()
        date_str = datetime.now().strftime('%Y%m%d')
        return logs_dir / f"tencent_risk_{account_type}_{date_str}.log"
    
    @staticmethod
    def get_upload_log_filename() -> Path:
        """获取上传日志文件名"""
        logs_dir = FileManager.get_logs_directory()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return logs_dir / f"upload_log_{timestamp}.log"
    
    @staticmethod
    def save_kuaishou_upload_log(success_count: int, fail_count: int, 
                               total_videos: int, log_content: str = ""):
        """保存快手上传日志"""
        log_file = FileManager.get_kuaishou_upload_log_filename()
        
        try:
            with open(log_file, "w", encoding='utf-8') as f:
                f.write(f"快手上传日志 - {datetime.now()}\n")
                f.write(f"总视频: {total_videos}\n")
                f.write(f"成功: {success_count}, 失败: {fail_count}\n")
                if log_content:
                    f.write(f"\n详细日志:\n{log_content}")
        except Exception as e:
            print(f"⚠️  保存快手日志失败: {e}")
    
    @staticmethod
    def create_upload_session_log():
        """创建上传会话日志"""
        log_file = FileManager.get_upload_log_filename()
        
        try:
            with open(log_file, "w", encoding='utf-8') as f:
                f.write(f"多平台上传会话 - {datetime.now()}\n")
                f.write("=" * 60 + "\n")
            return log_file
        except Exception as e:
            print(f"⚠️  创建上传日志失败: {e}")
            return None
    
    @staticmethod
    def add_log_entry(log_file: Path, message: str):
        """添加日志条目"""
        try:
            with open(log_file, "a", encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        except Exception as e:
            print(f"⚠️  写入日志失败: {e}")
    
    @staticmethod
    def create_cookie_directory(platform: str) -> Path:
        """为指定平台创建Cookie目录"""
        cookies_dir = FileManager.get_cookies_directory() / f"{platform}_uploader"
        cookies_dir.mkdir(parents=True, exist_ok=True)
        return cookies_dir
    
    @staticmethod
    def check_cookie_file_exists(platform: str) -> bool:
        """检查Cookie文件是否存在"""
        cookie_path = PlatformManager.get_cookie_path(platform)
        return cookie_path and cookie_path.exists()
    
    @staticmethod
    def get_file_size_string(file_path: Path) -> str:
        """获取文件大小字符串表示"""
        try:
            size_bytes = file_path.stat().st_size
            
            if size_bytes < 1024:
                return f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f}KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f}MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"
        except Exception:
            return "未知大小"
    
    @staticmethod
    def get_video_files_with_info(directory: Optional[Path] = None) -> List[Dict]:
        """获取带信息的视频文件列表"""
        video_files = FileManager.find_video_files(directory)
        
        videos_info = []
        for video_file in video_files:
            # 检查是否有对应的缩略图
            thumbnail_path = video_file.with_suffix('.png')
            has_thumbnail = thumbnail_path.exists()
            
            videos_info.append({
                'path': video_file,
                'name': video_file.name,
                'size': FileManager.get_file_size_string(video_file),
                'has_thumbnail': has_thumbnail
            })
        
        return videos_info


# 注意：这里需要导入PlatformManager，但为了避免循环导入，在方法内部使用
try:
    from utils.scheduler.platform_manager import PlatformManager
except ImportError:
    PlatformManager = None