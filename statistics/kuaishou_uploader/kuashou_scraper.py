#!/usr/bin/env python3
"""
快手数据爬取器
从快手统计页面获取账号视频数据
"""

import asyncio
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from playwright.async_api import async_playwright
from utils.base_social_media import set_init_script
from utils.log import kuaishou_logger
from conf import LOCAL_CHROME_PATH


class KuaishouScraper:
    """快手数据爬取器
    
    爬取快手创作者平台的统计信息，包括：
    - 作品统计: https://cp.kuaishou.com/statistics/works
    - 账号概览: 账号总览页面
    - 视频详情: 每个视频的详细统计
    """
    
    def __init__(self, account_file: str, local_executable_path: str = None):
        self.account_file = str(account_file)
        self.local_executable_path = local_executable_path or LOCAL_CHROME_PATH
        self.timeout = 30
        self.base_url = "https://cp.kuaishou.com"
        
    def _launch_browser(self, playwright):
        """启动浏览器"""
        if self.local_executable_path:
            return playwright.chromium.launch(
                headless=False,
                executable_path=self.local_executable_path
            )
        else:
            return playwright.chromium.launch(headless=False)
    
    async def validate_cookie(self) -> bool:
        """验证Cookie是否有效"""
        try:
            async with async_playwright() as playwright:
                browser = self._launch_browser(playwright)
                context = await browser.new_context(storage_state=self.account_file)
                context = await set_init_script(context)
                
                page = await context.new_page()
                
                # 访问统计页面检查登录状态
                await page.goto(f"{self.base_url}/statistics/works")
                await page.wait_for_load_state("networkidle")
                
                # 检查是否需要登录
                login_elements = page.locator('[class*="login"], [class*="login-button"]')
                if await login_elements.count() > 0:
                    kuaishou_logger.warning("需要重新登录")
                    return False
                
                # 检查是否能访问统计数据
                content_area = page.locator('.content-area, .k-table')
                if await content_area.count() == 0:
                    kuaishou_logger.warning("无法访问统计数据")
                    return False
                
                return True
                
        except Exception as e:
            kuaishou_logger.error(f"Cookie验证失败: {e}")
            return False
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """获取账号概览数据"""
        try:
            async with async_playwright() as playwright:
                browser = self._launch_browser(playwright)
                context = await browser.new_context(storage_state=self.account_file)
                context = await set_init_script(context)
                
                page = await context.new_page()
                
                # 访问作品统计页面
                await page.goto(f"{self.base_url}/statistics/works")
                await page.wait_for_timeout(3000)  # 等待页面加载
                
                summary = {
                    'account_name': '快手账号',
                    'account_id': '',
                    'total_videos': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'total_shares': 0,
                    'total_collections': 0,
                    'followers': 0,
                    'following': 0,
                    'total_earnings': Decimal('0.00')
                }
                
                # 提取账号信息
                account_name = await page.locator('.user-name .name').text_content()
                if account_name:
                    summary['account_name'] = account_name.strip()
                
                # 提取粉丝关注数据
                try:
                    follower_elements = page.locator('.fans-count, .k-card-overview .number')
                    if await follower_elements.count() > 0:
                        followers_text = await follower_elements.first.text_content()
                        if followers_text and followers_text.strip().replace(',', '').isdigit():
                            summary['followers'] = int(followers_text.strip().replace(',', ''))
                except:
                    pass
                
                # 提取作品集统计
                try:
                    stat_containers = page.locator('.k-card, .stat-card')
                    
                    async for container in stat_containers.all():
                        title_elem = await container.locator('.title, .k-card-subtitle').text_content()
                        if title_elem:
                            title = title_elem.strip().lower()
                            value_elem = await container.locator('.value, .k-card-meta').text_content()
                            if value_elem:
                                value = value_elem.strip().replace(',', '')
                                if value.isdigit():
                                    num_value = int(value)
                                    
                                    # 根据标题匹配数据
                                    if '作品' in title or '视频' in title:
                                        summary['total_videos'] = num_value
                                    elif '播放' in title or '观看' in title:
                                        summary['total_views'] = num_value
                                    elif '点赞' in title:
                                        summary['total_likes'] = num_value
                                    elif '评论' in title:
                                        summary['total_comments'] = num_value
                                    elif '分享' in title:
                                        summary['total_shares'] = num_value
                except:
                    pass
                
                # 备选方案：从JavaScript变量中提取数据
                js_data = await page.evaluate("""
                    () => {
                        let data = {};
                        
                        // 尝试从全局变量中获取
                        if (window.__INITIAL_STATE__) {
                            data = window.__INITIAL_STATE__;
                        }
                        
                        // 尝试从meta标签获取
                        const metaTags = document.querySelectorAll('meta');
                        for (let meta of metaTags) {
                            const name = meta.getAttribute('name');
                            const content = meta.getAttribute('content');
                            if (name && content) {
                                data[name] = content;
                            }
                        }
                        
                        return data;
                    }
                """)
                
                if js_data and isinstance(js_data, dict):
                    for key, value in js_data.items():
                        if isinstance(value, str) and value.isdigit():
                            num_value = int(value)
                            
                            if 'totalViews' in key:
                                summary['total_views'] = num_value
                            elif 'totalLikes' in key:
                                summary['total_likes'] = num_value
                
                return summary
                
        except Exception as e:
            kuaishou_logger.error(f"获取账号概览数据失败: {e}")
            # 返回空数据但保证程序继续
            return {
                'account_name': '快手账号',
                'account_id': '',
                'total_videos': 0,
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0,
                'total_collections': 0,
                'followers': 0,
                'following': 0,
                'total_earnings': Decimal('0.00')
            }
    
    async def get_video_details(self) -> List[Dict[str, Any]]:
        """获取视频详情列表"""
        try:
            async with async_playwright() as playwright:
                browser = self._launch_browser(playwright)
                context = await browser.new_context(storage_state=self.account_file)
                context = await set_init_script(context)
                
                page = await context.new_page()
                
                # 访问作品管理页面
                await page.goto(f"{self.base_url}/article/manage/video")
                await page.wait_for_timeout(3000)
                
                videos = []
                video_rows = page.locator('tbody tr')
                
                if await video_rows.count() > 0:
                    async for row in video_rows.all():
                        video = await self._extract_video_data(row)
                        if video:
                            videos.append(video)
                
                return videos
                
        except Exception as e:
            kuaishou_logger.error(f"获取视频详则失败: {e}")
            return []
    
    async def _extract_video_data(self, row) -> Optional[Dict[str, Any]]:
        """提取单行视频数据"""
        try:
            # 基本信息
            title = await row.locator('.title, .video-title').text_content()
            views = await row.locator('.views, .play-count').text_content()
            likes = await row.locator('.likes, .like-count').text_content()
            comments = await row.locator('.comments, .comment-count').text_content()
            
            # 收集链接
            link_elem = row.locator('a[href*="/analytics/video"]')
            video_link = await link_elem.get_attribute('href') if await link_elem.count() > 0 else ""
            video_id = video_link.split('/')[-1] if video_link else ""
            
            return {
                'video_id': video_id,
                'title': title.strip() if title else "",
                'views': int(views.strip().replace(',', '')) if views and views.strip().replace(',', '').isdigit() else 0,
                'likes': int(likes.strip().replace(',', '')) if likes and likes.strip().replace(',', '').isdigit() else 0,
                'comments': int(comments.strip().replace(',', '')) if comments and comments.strip().replace(',', '').isdigit() else 0,
                'shares': 0,  # 默认，后续可以查找
                'collections': 0,  # 默认，后续可以查找
                'upload_time': datetime.now().isoformat()  # 默认当前时间，实际应从时间戳获取
            }
            
        except Exception as e:
            kuaishou_logger.debug(f"提取视频数据失败: {e}")
            return None
    
    async def collect_statistics(self) -> Dict[str, Any]:
        """收集完整的快手统计信息
        
        Returns:
            包含账号和视频统计的完整数据
        """
        kuaishou_logger.info("开始收集快手统计数据...")
        start_time = datetime.now()
        
        try:
            # 获取账号概况
            account_summary = await self.get_account_summary()
            
            # 获取视频详情
            video_details = await self.get_video_details()
            
            # 数据处理和统计
            processed_videos = []
            for video in video_details:
                if video:
                    video['like_rate'] = round((video['likes'] / max(video['views'], 1)) * 100, 2)
                    processed_videos.append(video)
            
            elapsed = datetime.now() - start_time
            
            return {
                'platform': 'kuaishou',
                'account_summary': account_summary,
                'video_details': processed_videos,
                'metadata': {
                    'collection_time': datetime.now().isoformat(),
                    'processing_time': elapsed.total_seconds(),
                    'total_videos': len(processed_videos),
                    'data_source': '快手创作者平台',
                    'platform_url': 'https://cp.kuaishou.com/statistics/works'
                }
            }
            
        except Exception as e:
            kuaishou_logger.error(f"收集统计数据失败: {e}")
            return {
                'platform': 'kuaishou',
                'account_summary': {
                    'account_name': '快手账号',
                    'total_videos': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'followers': 0
                },
                'video_details': [],
                'metadata': {
                    'collection_time': datetime.now().isoformat(),
                    'error': str(e)
                }
            }


# 快捷函数
def get_kuaishou_statistics(account_file: str) -> Dict[str, Any]:
    """快速获取快手统计数据的函数
    
    Args:
        account_file: Cookie文件路径
        
    Returns:
        统计数据字典
    """
    
    async def _get_stats():
        scraper = KuaishouScraper(account_file)
        return await scraper.collect_statistics()
    
    return asyncio.run(_get_stats())