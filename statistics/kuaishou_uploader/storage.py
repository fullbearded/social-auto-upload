#!/usr/bin/env python3
"""
快手数据存储管理器
提供数据的持久化存储、版本管理和数据查询功能
"""

import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from conf import BASE_DIR
from utils.log import kuaishou_logger


class KuaishouDataStorage:
    """快手数据存储管理器"""
    
    def __init__(self, database_path: Optional[str] = None):
        self.db_path = Path(database_path or BASE_DIR / "data" / "kuaishou_stats.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化存储数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 账号信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT UNIQUE,
                account_name TEXT,
                followers INTEGER DEFAULT 0,
                total_videos INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                total_collections INTEGER DEFAULT 0,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_hash TEXT UNIQUE
            )
        ''')
        
        # 视频统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                video_id TEXT,
                title TEXT,
                upload_time DATETIME,
                publish_time DATETIME,
                status TEXT DEFAULT 'normal',
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                collections INTEGER DEFAULT 0,
                new_followers INTEGER DEFAULT 0,
                earnings REAL DEFAULT 0.0,
                like_rate REAL DEFAULT 0.0,
                comment_rate REAL DEFAULT 0.0,
                share_rate REAL DEFAULT 0.0,
                collection_rate REAL DEFAULT 0.0,
                collection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_hash TEXT UNIQUE,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        ''')
        
        # 每日统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                stat_date DATE,
                videos_published INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                new_followers INTEGER DEFAULT 0,
                earnings REAL DEFAULT 0.0,
                collection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        ''')
        
        # 数据版本表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                collection_date DATETIME,
                data_type TEXT,
                data_hash TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        kuaishou_logger.info("快手数据存储数据库初始化完成")
    
    def save_account_summary(self, summary: Dict[str, Any]) -> bool:
        """保存账号概要数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 生成数据哈希
            data_str = f"{summary['account_name']}{summary['total_views']}{summary['followers']}"
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            cursor.execute('''
                INSERT OR REPLACE INTO accounts 
                (account_id, account_name, followers, total_videos, total_views, total_likes, 
                 total_comments, total_shares, total_collections, last_update, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary.get('account_name', 'ks_account'),
                summary.get('account_name', '快手账号'),
                summary.get('followers', 0),
                summary.get('total_videos', 0),
                summary.get('total_views', 0),
                summary.get('total_likes', 0),
                summary.get('total_comments', 0),
                summary.get('total_shares', 0),
                summary.get('total_collections', 0),
                datetime.now(),
                data_hash
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            kuaishou_logger.error(f"保存账号概要失败: {e}")
            return False
    
    def save_video_details(self, account_id: str, video_details: List[Dict[str, Any]]) -> bool:
        """保存视频详细数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 标记旧数据为历史版本
            cursor.execute('''
                UPDATE videos SET collection_date = ? 
                WHERE account_id = ? AND collection_date < date('now', '-1 day')
            ''', (datetime.now(), account_id))
            
            # 插入新数据
            for video in video_details:
                if not video.get('video_id'):
                    continue
                
                data_str = f"{account_id}{video['video_id']}{video.get('views', 0)}"
                data_hash = hashlib.md5(data_str.encode()).hexdigest()
                
                upload_time = video.get('upload_time') or datetime.now()
                if isinstance(upload_time, str):
                    try:
                        upload_time = datetime.fromisoformat(upload_time)
                    except:
                        upload_time = datetime.now()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO videos
                    (account_id, video_id, title, upload_time, views, likes, comments, 
                     shares, collections, new_followers, earnings, like_rate, comment_rate, 
                     share_rate, collection_rate, collection_date, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    video.get('video_id', ''),
                    video.get('title', ''),
                    upload_time,
                    video.get('views', 0),
                    video.get('likes', 0),
                    video.get('comments', 0),
                    video.get('shares', 0),
                    video.get('collections', 0),
                    video.get('new_followers', 0),
                    float(video.get('earnings', 0.0)),
                    video.get('like_rate', 0.0),
                    video.get('comment_rate', 0.0),
                    video.get('share_rate', 0.0),
                    video.get('collection_rate', 0.0),
                    datetime.now(),
                    data_hash
                ))
            
            conn.commit()
            conn.close()
            kuaishou_logger.info(f"已保存 {len(video_details)} 个视频数据")
            return True
            
        except Exception as e:
            kuaishou_logger.error(f"保存视频详细数据失败: {e}")
            return False
    
    def get_account_history(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取账号的历史数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM accounts
                WHERE account_id = ?
                ORDER BY last_update DESC
                LIMIT ?
            ''', (account_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            kuaishou_logger.error(f"获取账号历史失败: {e}")
            return []
    
    def get_video_performance(self, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取视频表现数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM videos
                WHERE account_id = ?
                ORDER BY views DESC
                LIMIT ?
            ''', (account_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            kuaishou_logger.error(f"获取视频表现失败: {e}")
            return []
    
    def get_trend_data(self, account_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取趋势数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    date(collection_date) as date,
                    COUNT(*) as videos_uploaded,
                    SUM(views) as total_views,
                    AVG(views) as avg_views,
                    AVG(like_rate) as avg_like_rate
                FROM videos
                WHERE account_id = ? 
                  AND collection_date >= date('now', '-{} days')
                GROUP BY date(collection_date)
                ORDER BY date ASC
            '''.format(days), (account_id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            kuaishou_logger.error(f"获取趋势数据失败: {e}")
            return []
    
    def export_to_json(self, account_id: str, output_path: str) -> bool:
        """导出数据到JSON"""
        try:
            account_data = {
                'account_summary': self.get_account_history(account_id, 1),
                'video_details': self.get_video_performance(account_id),
                'export_time': datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(account_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            kuaishou_logger.error(f"导出JSON失败: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90) -> bool:
        """清理旧数据"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                DELETE FROM videos 
                WHERE collection_date < ?
            ''', (cutoff_date,))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            kuaishou_logger.info(f"已清理 {affected} 条旧数据")
            return True
            
        except Exception as e:
            kuaishou_logger.error(f"清理旧数据失败: {e}")
            return False