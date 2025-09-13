#!/usr/bin/env python3
"""
快手数据统计采集器
自动从快手创作者平台采集账号和视频数据
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from decimal import Decimal
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext, Page
from utils.base_social_media import set_init_script
from conf import LOCAL_CHROME_PATH
from utils.log import kuaishou_logger

from .data_structures import (
    KuaishouVideoStats, 
    KuaishouAccountSummary,
    KuaishouAPIResponse,
    KuaishouEndpoints
)


class KuaishouStatisticsScraper:
    """快手数据统计采集器"""
    
    def __init__(self, cookie_path: str, local_executable_path: str = None):
        self.cookie_path = Path(cookie_path)
        self.local_executable_path = local_executable_path or LOCAL_CHROME_PATH
        self.timeout_seconds = 30
        
    async def validate_cookie(self) -> bool:
        """验证Cookie有效性"""
        try:
            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                context = await browser.new_context(storage_state=str(self.cookie_path))
                context = await set_init_script(context)
                
                page = await context.new_page()
                await page.goto(KuaishouEndpoints.OVERVIEW)
                
                # 检查是否需要登录
                login_indicator = page.locator('div.login-container')
                if await login_indicator.count() > 0:
                    kuaishou_logger.error("Cookie已失效，需要重新登录")
                    return False
                    
                return True
                
        except Exception as e:
            kuaishou_logger.error(f"Cookie验证失败: {e}")
            return False
    
    async def get_account_summary(self) -> KuaishouAccountSummary:
        """获取账号概览数据"""
        summary = KuaishouAccountSummary()
        
        try:
            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                context = await browser.new_context(storage_state=str(self.cookie_path))
                context = await set_init_script(context)
                
                page = await context.new_page()
                
                # 获取账号基本信息
                await page.goto(KuaishouEndpoints.OVERVIEW)
                await page.wait_for_load_state("networkidle")
                
                # 获取账号名和ID
                try:
                    account_name = await page.locator('.user-name .name').text_content()
                    summary.account_name = account_name.strip() if account_name else ""
                except:
                    summary.account_name = "Unknown"
                
                # 获取关注数据
                try:
                    follower_text = await page.locator('.k-card-overview .number').first.text_content()
                    if follower_text:
                        summary.followers = int(follower_text.replace(',', ''))
                except:
                    summary.followers = 0
                
                # 获取总体统计
                await page.goto(KuaishouEndpoints.WORKS_STATISTICS)
                await page.wait_for_load_state("networkidle")
                
                # 等待数据加载
                await asyncio.sleep(3)
                
                # 获取视频总数
                try:
                    total_selector = 'div.card-container .total-count'
                    total_text = await page.locator(total_selector).text_content()
                    if total_text:
                        match = re.search(r'(\d+)', total_text)
                        if match:
                            summary.total_videos = int(match.group(1))
                except:
                    summary.total_videos = 0
                
                # 获取播放和互动总量
                await self._extract_total_stats_from_bindings(page, summary)
                
                summary.last_update = datetime.now()
                
        except Exception as e:
            kuaishou_logger.error(f"获取账号概览失败: {e}")
            raise
        
        return summary
    
    async def get_video_detail_stats(self, video_filter: str = "all") -> List[KuaishouVideoStats]:
        """获取详细的视频统计数据"""
        videos = []
        
        try:
            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                context = await browser.new_context(storage_state=str(self.cookie_path))
                context = await set_init_script(context)
                
                page = await context.new_page()
                await page.goto(KuaishouEndpoints.CONTENT_LIST)
                await page.wait_for_load_state("networkidle")
                
                # 等待内容加载
                await asyncio.sleep(2)
                
                # 如果有大量视频，可能需要分页加载
                await self._load_all_videos_on_page(page)
                
                # 获取所有视频行
                video_rows = await page.locator('table tbody tr').all()
                
                for row in video_rows:
                    video = await self._parse_video_row(row)
                    if video:
                        videos.append(video)
                
        except Exception as e:
            kuaishou_logger.error(f"获取视频详细数据失败: {e}")
            raise
        
        return videos
    
    async def get_recent_performance(self, days: int = 30) -> Dict[str, any]:
        """获取近期表现数据"""
        try:
            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                context = await browser.new_context(storage_state=str(self.cookie_path))
                context = await set_init_script(context)
                
                page = await context.new_page()
                await page.goto(KuaishouEndpoints.DETAIL_DASHBOARD)
                await page.wait_for_load_state("networkidle")
                
                # 设置时间范围
                await self._set_date_range(page, days)
                
                # 获取图表数据
                return await self._extract_chart_data(page, days)
                
        except Exception as e:
            kuaishou_logger.error(f"获取近期表现失败: {e}")
            return {}
    
    async def _launch_browser(self, playwright):
        """启动浏览器"""
        if self.local_executable_path:
            return await playwright.chromium.launch(
                headless=False,
                executable_path=self.local_executable_path
            )
        else:
            return await playwright.chromium.launch(headless=False)
    
    async def _extract_total_stats_from_bindings(self, page: Page, summary: KuaishouAccountSummary):
        """从页面绑定数据中提取统计信息"""
        try:
            # 执行JavaScript获取Vue/Mobx中的数据
            js_code = """
                    () => {
                        // 尝试从不同的数据源读取
                        const vueData = window.__INITIAL_STATE__ || {};
                        const mobxData = window.mobxStore || {};
                        
                        // 合并数据
                        const data = {...vueData, ...mobxData};
                        
                        // 提取统计信息
                        return {
                            totalViews: data.totalViews || 0,
                            totalLikes: data.totalLikes || 0,
                            totalComments: data.totalComments || 0,
                            totalShares: data.totalShares || 0
                        };
                    }
                """
            
            stats = await page.evaluate(js_code)
            
            summary.total_views = int(stats.get('totalViews', 0))
            summary.total_likes = int(stats.get('totalLikes', 0))
            summary.total_comments = int(stats.get('totalComments', 0))
            summary.total_shares = int(stats.get('totalShares', 0))
            
        except Exception:
            # 备用：从页面元素读取
            await self._extract_stats_from_elements(page, summary)
    
    async def _extract_stats_from_elements(self, page: Page, summary: KuaishouAccountSummary):
        """从页面元素中提取统计信息"""
        try:
            # 尝试从卡片元素中提取数据
            stat_cards = await page.locator('.stat-card, .k-card').all()
            
            for card in stat_cards:
                title = await card.locator('.title, .stat-title').text_content()
                value_text = await card.locator('.value, .number').text_content()
                
                if title and value_text:
                    value = int(value_text.replace(',', ''))
                    title_lower = title.lower()
                    
                    if '播放' in title_lower or '观看' in title_lower:
                        summary.total_views = value
                    elif '点赞' in title_lower:
                        summary.total_likes = value
                    elif '评论' in title_lower:
                        summary.total_comments = value
                    elif '分享' in title_lower:
                        summary.total_shares = value
                        
        except Exception as e:
            kuaishou_logger.warning(f"从元素提取统计失败: {e}")
    
    async def _load_all_videos_on_page(self, page: Page):
        """加载页面上的所有视频（处理分页）"""
        scroll_attempts = 0
        max_attempts = 5
        
        while scroll_attempts < max_attempts:
            try:
                # 检查是否有加载更多按钮
                load_more = page.locator('button:has-text("加载更多")')
                if await load_more.count() > 0 and await load_more.is_visible():
                    await load_more.click()
                    await asyncio.sleep(2)
                else:
                    # 尝试滚动加载
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                    
                scroll_attempts += 1
            except:
                break
    
    async def _parse_video_row(self, row) -> Optional[KuaishouVideoStats]:
        """解析单行视频数据"""
        try:
            video = KuaishouVideoStats()
            
            # 获取标题
            title_elem = await row.locator('.title, .video-title').text_content()
            video.title = title_elem.strip() if title_elem else ""
            
            # 获取视频链接/ID
            link_elem = row.locator('a[href*="/analytics/video"]')
            href = await link_elem.get_attribute('href') if await link_elem.count() > 0 else ""
            if href:
                video.video_id = href.split('/')[-1]
            
            # 获取上传时间
            upload_time_elem = await row.locator('.upload-time, .time').text_content()
            if upload_time_elem:
                try:
                    video.upload_time = datetime.fromisoformat(upload_time_elem.strip())
                except:
                    pass
            
            # 获取播放量
            views_elem = await row.locator('.views, .play-count').text_content()
            if views_elem:
                views_text = views_elem.strip().replace(',', '')
                video.views = int(views_text) if views_text.isdigit() else 0
            
            # 获取点赞量
            likes_elem = await row.locator('.likes, .like-count').text_content()
            if likes_elem:
                likes_text = likes_elem.strip().replace(',', '')
                video.likes = int(likes_text) if likes_text.isdigit() else 0
            
            # 获取评论量
            comments_elem = await row.locator('.comments, .comment-count').text_content()
            if comments_elem:
                comments_text = comments_elem.strip().replace(',', '')
                video.comments = int(comments_text) if comments_text.isdigit() else 0
            
            # 获取分享量
            shares_elem = await row.locator('.shares, .share-count').text_content()
            if shares_elem:
                shares_text = shares_elem.strip().replace(',', '')
                video.shares = int(shares_text) if shares_text.isdigit() else 0
            
            # 计算比率
            video.calculate_rates()
            
            return video
            
        except Exception as e:
            kuaishou_logger.warning(f"解析视频行失败: {e}")
            return None
    
    async def _set_date_range(self, page: Page, days: int):
        """设置统计时间范围"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 找到日期选择器并设置范围
            date_pickers = page.locator('.date-picker, .ant-picker')
            
            if await date_pickers.count() > 0:
                await date_pickers.first.click()
                await asyncio.sleep(1)
                
                # 输入开始日期
                date_inputs = page.locator('.ant-picker-input input')
                if await date_inputs.count() >= 2:
                    await date_inputs.first.fill(start_date.strftime("%Y-%m-%d"))
                    await date_inputs.last.fill(end_date.strftime("%Y-%m-%d"))
                    
                    # 确认选择
                    confirm_btn = page.locator('.ant-picker-ok button')
                    if await confirm_btn.count() > 0:
                        await confirm_btn.click()
                    
                    await asyncio.sleep(2)
                    
        except Exception as e:
            kuaishou_logger.warning(f"设置日期范围失败: {e}")
    
    async def _extract_chart_data(self, page: Page, days: int) -> Dict[str, any]:
        """提取图表数据"""
        try:
            chart_data = {}
            
            # 等待图表加载
            await asyncio.sleep(3)
            
            # 提取趋势数据
            trend_script = f"""
                    () => {{
                        const chartData = window.chartData || window.trendData || {};
                        const {days}dData = [];
                        
                        if (Array.isArray(chartData)) {{
                            return chartData.slice(-{days});
                        }}
                        
                        return [];
                    }}
                """
            
            chart_data['trend'] = await page.evaluate(trend_script)
            
            return chart_data
            
        except Exception as e:
            kuaishou_logger.warning(f"提取图表数据失败: {e}")
            return {}
    
    async def collect_all_data(self) -> Dict[str, any]:
        """采集所有快手统计数据的完整方法"""
        start_time = datetime.now()
        kuaishou_logger.info("开始快手数据收集...")
        
        try:
            # 1. 验证Cookie
            if not await self.validate_cookie():
                return {
                    'error': 'Cookie验证失败，请重新登录',
                    'timestamp': start_time.isoformat()
                }
            
            # 2. 获取账号概览
            account_summary = await self.get_account_summary()
            
            # 3. 获取视频详细数据
            video_details = await self.get_video_detail_stats()
            
            # 4. 获取近期表现
            recent_performance = await self.get_recent_performance(days=30)
            
            elapsed = datetime.now() - start_time
            kuaishou_logger.info(f"数据收集完成，耗时 {elapsed.total_seconds():.2f} 秒")
            
            return {
                'account_summary': {
                    'account_name': account_summary.account_name,
                    'total_videos': account_summary.total_videos,
                    'total_views': account_summary.total_views,
                    'total_likes': account_summary.total_likes,
                    'total_comments': account_summary.total_comments,
                    'total_shares': account_summary.total_shares,
                    'followers': account_summary.followers
                },
                'video_details': [
                    {
                        'video_id': video.video_id,
                        'title': video.title,
                        'views': video.views,
                        'likes': video.likes,
                        'comments': video.comments,
                        'shares': video.shares,
                        'like_rate': round(video.like_rate, 2),
                        'upload_time': video.upload_time.isoformat() if video.upload_time else None
                    }
                    for video in video_details
                ],
                'total_videos_found': len(video_details),
                'collection_time': datetime.now().isoformat(),
                'processing_time': elapsed.total_seconds()
            }
            
        except Exception as e:
            kuaishou_logger.error(f"数据收集失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


async def get_kuaishou_statistics(cookie_path: str) -> Dict[str, Any]:
    """快手数据统计的快速访问函数"""
    scraper = KuaishouStatisticsScraper(cookie_path)
    return await scraper.collect_all_data()