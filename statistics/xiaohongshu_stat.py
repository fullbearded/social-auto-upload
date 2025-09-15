#!/usr/bin/env python3
"""
小红书统计模块 - 支持获取小红书账号统计数据
Xiaohongshu Statistics Module - Supports fetching Xiaohongshu account statistics
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page
from conf import LOCAL_CHROME_PATH

# 日志配置
import logging
xiaohongshu_logger = logging.getLogger('xiaohongshu_stat')


class XiaohongshuStatsError(Exception):
    """小红书统计异常"""
    pass


async def get_xiaohongshu_statistics(cookie_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    获取小红书账号统计数据
    
    Args:
        cookie_path: Cookie文件路径
        debug: 是否启用调试模式
    
    Returns:
        统计数据字典，失败返回None
    """
    
    if not Path(LOCAL_CHROME_PATH).exists():
        xiaohongshu_logger.error(f"Chrome 浏览器未找到: {LOCAL_CHROME_PATH}")
        raise XiaohongshuStatsError(f"Chrome 浏览器未找到: {LOCAL_CHROME_PATH}")
    
    if not Path(cookie_path).exists():
        xiaohongshu_logger.error(f"Cookie 文件未找到: {cookie_path}")
        raise XiaohongshuStatsError(f"Cookie 文件未找到: {cookie_path}")
    
    browser = None
    try:
        # 读取Cookie文件
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        
        if not cookie_data:
            xiaohongshu_logger.error("Cookie 文件为空")
            raise XiaohongshuStatsError("Cookie 文件为空")
        
        async with async_playwright() as playwright:
            # 启动浏览器配置
            if debug:
                launch_options = {
                    'headless': False,
                    'executable_path': LOCAL_CHROME_PATH,
                    'args': ['--disable-blink-features=AutomationControlled']
                }
            else:
                launch_options = {
                    'headless': True,
                    'args': [
                        '--headless=new',
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                }
                
                # 如果有Chrome路径，添加它
                if LOCAL_CHROME_PATH:
                    launch_options['executable_path'] = LOCAL_CHROME_PATH
            
            browser = await playwright.chromium.launch(**launch_options)
            
            # 创建context并设置Cookie
            context = await browser.new_context()
            
            # 设置Cookie
            if isinstance(cookie_data, dict) and 'cookies' in cookie_data:
                # 小红书格式：包含cookies数组的对象
                await context.add_cookies(cookie_data['cookies'])
            elif isinstance(cookie_data, list):
                # 标准列表格式
                await context.add_cookies(cookie_data)
            elif isinstance(cookie_data, dict):
                # 字典格式，转换为Playwright格式
                playwright_cookies = []
                for name, value in cookie_data.items():
                    playwright_cookies.append({
                        'name': name,
                        'value': str(value),
                        'domain': '.xiaohongshu.com',
                        'path': '/',
                        'expires': -1,
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'Lax'
                    })
                await context.add_cookies(playwright_cookies)
            
            page = await context.new_page()
            
            # 设置用户代理和额外头部
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            })
            
            # 访问小红书创作者中心
            try:
                await page.goto('https://www.xiaohongshu.com/creator-center', wait_until='networkidle', timeout=60000)
                await page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(3)  # 等待页面完全加载
            except Exception as e:
                print(f"⚠️  页面访问超时，尝试备用URL...")
                # 尝试备用URL
                await page.goto('https://www.xiaohongshu.com', wait_until='networkidle', timeout=60000)
                await page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(3)
            
            # 检查是否登录成功
            if "login" in page.url or await page.locator('text="登录"').count() > 0:
                raise XiaohongshuStatsError("Cookie已失效，需要重新登录")
            
            # 获取统计数据
            stats_data = await _extract_xiaohongshu_stats(page)
            
            # 如果是调试模式，暂停执行
            if debug:
                xiaohongshu_logger.info("🔍 调试模式：浏览器将保持打开状态")
                xiaohongshu_logger.info("请在浏览器中检查数据，然后按回车键继续...")
                await page.pause()
            
            return stats_data
            
    except Exception as e:
        # 调试模式下，即使出错也要保持浏览器打开
        if debug:
            print(f"❌ 获取 xiaohongshu 统计数据时出错: 获取小红书统计数据失败: {e}")
            print("🔍 调试模式已启用，浏览器将保持打开状态以便调试")
            print("请在浏览器中检查问题，然后按回车键继续...")
            if 'page' in locals():
                await page.pause()
        raise XiaohongshuStatsError(f"获取小红书统计数据失败: {e}")
    finally:
        # 非调试模式下关闭浏览器
        if browser and not debug:
            await browser.close()


async def _extract_xiaohongshu_stats(page: Page) -> Dict[str, Any]:
    """从小红书页面提取统计数据"""
    stats_data = {
        'platform': 'xiaohongshu',
        'account_name': '',
        'followers': 0,
        'following': 0,
        'likes': 0,
        'videos_count': 0,
        'notes_count': 0,  # 小红书特有的笔记数
        'timestamp': '',
        'raw_data': {}
    }
    
    try:
        xiaohongshu_logger.info("开始提取小红书数据...")
        
        # 首先尝试访问个人主页或数据中心
        await _navigate_to_stats_page(page)
        await asyncio.sleep(3)
        
        # 提取账号基本信息
        try:
            account_info = await page.evaluate('''
                () => {
                    const result = {
                        name: '',
                        followers: 0,
                        following: 0,
                        likes: 0,
                        notes: 0
                    };
                    
                    // 获取账号名称 - 使用实际的页面结构
                    const nameElement = document.querySelector('.account-name');
                    if (nameElement && nameElement.textContent.trim()) {
                        result.name = nameElement.textContent.trim();
                    }
                    
                    return result;
                }
            ''')
            
            stats_data['account_name'] = account_info.get('name', '')
            
        except Exception as e:
            xiaohongshu_logger.warning(f"获取账号信息失败: {e}")
        
        # 主要数据提取 - 基于实际页面结构
        main_stats = await page.evaluate('''
            () => {
                const result = {
                    followers: 0,
                    following: 0,
                    likes: 0,
                    notes: 0
                };
                
                function parseChineseNumber(text) {
                    if (!text) return 0;
                    text = text.replace(/[^\\d.万kK]/g, '');
                    
                    if (text.includes('万') || text.includes('w') || text.includes('W')) {
                        return parseFloat(text.replace(/[万wW]/g, '')) * 10000;
                    } else if (text.includes('k') || text.includes('K')) {
                        return parseFloat(text.replace(/[kK]/g, '')) * 1000;
                    }
                    
                    return parseFloat(text) || 0;
                }
                
                // 基于实际页面结构提取数据
                // 查找包含统计信息的描述文本区域
                const descriptionText = document.querySelector('.description-text');
                if (descriptionText) {
                    // 查找所有包含数字的span元素
                    const numericalSpans = descriptionText.querySelectorAll('.numerical');
                    const textElements = Array.from(descriptionText.querySelectorAll('span'));
                    
                    textElements.forEach((element, index) => {
                        const text = element.textContent || '';
                        const numberText = text.trim();
                        
                        // 检查相邻的文本元素来确定数字类型
                        let nextElement = element.nextElementSibling;
                        let prevElement = element.previousElementSibling;
                        
                        if (element.classList.contains('numerical')) {
                            const number = parseChineseNumber(numberText);
                            
                            // 检查后续文本或前置文本来确定数字类型
                            if (nextElement && nextElement.textContent.includes('粉丝数')) {
                                result.followers = number;
                            } else if (nextElement && nextElement.textContent.includes('关注数')) {
                                result.following = number;
                            } else if (nextElement && nextElement.textContent.includes('获赞与收藏')) {
                                result.likes = number;
                            } else if (prevElement && prevElement.textContent.includes('粉丝数')) {
                                result.followers = number;
                            } else if (prevElement && prevElement.textContent.includes('关注数')) {
                                result.following = number;
                            } else if (prevElement && prevElement.textContent.includes('获赞与收藏')) {
                                result.likes = number;
                            }
                        }
                    });
                }
                
                // 如果没有在描述区域找到数据，尝试其他方法
                if (result.followers === 0 && result.following === 0) {
                    // 查找页面中所有的数字和标签组合
                    const allSpans = document.querySelectorAll('span');
                    const numbersAndLabels = [];
                    
                    allSpans.forEach(span => {
                        const text = span.textContent.trim();
                        const numberMatch = text.match(/(\\d+(?:\\.\\d+)?[万kK]?)/);
                        if (numberMatch) {
                            const number = parseChineseNumber(numberMatch[1]);
                            // 查找相邻的标签文本
                            let label = '';
                            let nextSibling = span.nextElementSibling;
                            let prevSibling = span.previousElementSibling;
                            
                            if (nextSibling && nextSibling.tagName === 'SPAN') {
                                label = nextSibling.textContent.trim();
                            } else if (prevSibling && prevSibling.tagName === 'SPAN') {
                                label = prevSibling.textContent.trim();
                            }
                            
                            if (label) {
                                numbersAndLabels.push({ number, label });
                            }
                        }
                    });
                    
                    // 根据标签匹配数据
                    numbersAndLabels.forEach(item => {
                        if (item.label.includes('粉丝') || item.label.includes('关注者')) {
                            result.followers = item.number;
                        } else if (item.label.includes('关注')) {
                            result.following = item.number;
                        } else if (item.label.includes('获赞') || item.label.includes('收藏') || item.label.includes('喜欢')) {
                            result.likes = item.number;
                        }
                    });
                }
                
                return result;
            }
        ''')
        
        stats_data['followers'] = main_stats.get('followers', 0)
        stats_data['following'] = main_stats.get('following', 0)
        stats_data['likes'] = main_stats.get('likes', 0)
        stats_data['notes_count'] = main_stats.get('notes', 0)
        
        # 尝试获取笔记数 - 从笔记数据总览页面获取
        try:
            notes_data = await page.evaluate('''
                () => {
                    // 首先查找其他区域是否有笔记数据
                    let notesCount = 0;
                    
                    // 查找包含笔记信息的元素
                    const notesSelectors = [
                        '[data-v-74d56742] .creator-block .number',
                        '.creator-block .number',
                        '.notes-count',
                        '.note-count',
                        '.works-count'
                    ];
                    
                    for (const selector of notesSelectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(element => {
                            const text = element.textContent || '';
                            const numberMatch = text.match(/(\\d+(?:\\.\\d+)?[万kK]?)/);
                            if (numberMatch) {
                                const number = this.parseChineseNumber ? this.parseChineseNumber(numberMatch[1]) : parseInt(numberMatch[1]) || 0;
                                if (number > notesCount) {
                                    notesCount = number;
                                }
                            }
                        });
                    }
                    
                    return notesCount;
                }
            ''')
            
            stats_data['notes_count'] = notes_data if notes_data > 0 else main_stats.get('notes', 0)
            
        except Exception as e:
            xiaohongshu_logger.warning(f"获取笔记数失败: {e}")
            stats_data['notes_count'] = main_stats.get('notes', 0)
        
        # 尝试获取笔记总数 - 从其他可能的区域获取
        try:
            # 如果还没有获取到笔记数，尝试从其他区域获取
            if stats_data['notes_count'] == 0:
                additional_notes_data = await page.evaluate('''
                    () => {
                        // 尝试从页面其他区域获取笔记总数
                        let totalNotes = 0;
                        
                        // 查找可能的笔记总数显示区域
                        const possibleSelectors = [
                            '.total-notes',
                            '.notes-total',
                            '.work-total',
                            '.content-total',
                            '[class*="total"]',
                            '.summary-number'
                        ];
                        
                        for (const selector of possibleSelectors) {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(element => {
                                const text = element.textContent || '';
                                const match = text.match(/(\\d+(?:\\.\\d+)?[万kK]?)/);
                                if (match) {
                                    const number = this.parseChineseNumber ? this.parseChineseNumber(match[1]) : parseInt(match[1]) || 0;
                                    if (number > totalNotes) {
                                        totalNotes = number;
                                    }
                                }
                            });
                        }
                        
                        // 如果还没有找到，尝试从页面标题或其他地方获取
                        if (totalNotes === 0) {
                            // 查找包含"篇"、"个"、"笔记"等关键词的文本
                            const allTextElements = document.querySelectorAll('span, div, p');
                            for (const element of allTextElements) {
                                const text = element.textContent || '';
                                if ((text.includes('篇') || text.includes('个') || text.includes('笔记')) && text.match(/\\d+/)) {
                                    const match = text.match(/(\\d+(?:\\.\\d+)?[万kK]?)/);
                                    if (match) {
                                        const number = this.parseChineseNumber ? this.parseChineseNumber(match[1]) : parseInt(match[1]) || 0;
                                        if (number > 0 && number < 1000000) { // 合理的笔记数范围
                                            totalNotes = number;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                        
                        return totalNotes;
                    }
                ''')
                
                if additional_notes_data > 0:
                    stats_data['notes_count'] = additional_notes_data
                    xiaohongshu_logger.info(f"从其他区域获取到笔记数: {additional_notes_data}")
        except Exception as e:
            xiaohongshu_logger.warning(f"从其他区域获取笔记数失败: {e}")
        
        # 尝试获取视频数（小红书可能没有单独的视频数）
        stats_data['videos_count'] = stats_data['notes_count']  # 小红书笔记就是视频
        
        # 设置时间戳
        from datetime import datetime
        stats_data['timestamp'] = datetime.now().isoformat()
        
        xiaohongshu_logger.info(f"小红书数据提取成功: 粉丝{stats_data['followers']:,} 关注{stats_data['following']:,} 获赞{stats_data['likes']:,} 笔记{stats_data['notes_count']:,}")
        
        # 验证数据
        if stats_data['followers'] == 0 and stats_data['following'] == 0:
            xiaohongshu_logger.warning("⚠️  获取到的数据可能不完整，页面结构可能已更新")
        
        return stats_data
        
    except Exception as e:
        xiaohongshu_logger.error(f"提取小红书数据时出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回部分数据，即使某些字段失败
        return stats_data


async def _navigate_to_stats_page(page: Page):
    """尝试导航到统计数据页面"""
    try:
        # 尝试查找并点击数据统计或个人中心入口
        navigation_attempts = [
            # 常见的统计数据入口
            {
                'selector': 'text="数据统计"',
                'description': '数据统计链接'
            },
            {
                'selector': 'text="数据中心"',
                'description': '数据中心链接'
            },
            {
                'selector': 'text="个人中心"',
                'description': '个人中心链接'
            },
            {
                'selector': 'text="我的主页"',
                'description': '我的主页链接'
            },
            {
                'selector': '.stats-link, .data-link, .profile-link',
                'description': '统计数据链接'
            }
        ]
        
        for attempt in navigation_attempts:
            try:
                elements = page.locator(attempt['selector'])
                if await elements.count() > 0:
                    await elements.first.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    xiaohongshu_logger.info(f"点击了 {attempt['description']}")
                    return
            except:
                continue
        
        # 如果没有找到统计数据入口，尝试访问常见的URL路径
        common_paths = [
            '/creator-micro/data',
            '/creator-micro/stats', 
            '/creator-micro/profile',
            '/stats',
            '/data',
            '/profile'
        ]
        
        current_url = page.url
        base_url = current_url.split('/')[0] + '//' + current_url.split('/')[2]
        
        for path in common_paths:
            try:
                await page.goto(base_url + path, {'waitUntil': 'networkidle'})
                await asyncio.sleep(2)
                
                # 检查页面是否加载成功
                if "login" not in page.url:
                    xiaohongshu_logger.info(f"成功访问数据页面: {path}")
                    return
            except:
                continue
        
        xiaohongshu_logger.info("保持在当前页面，尝试提取数据")
        
    except Exception as e:
        xiaohongshu_logger.warning(f"导航到统计页面失败: {e}")


# 测试函数
async def test_xiaohongshu_stats():
    """测试小红书统计功能"""
    print("🧪 测试小红书统计功能...")
    
    # 检查Cookie文件
    cookie_path = Path("cookies/xiaohongshu_uploader/account.json")
    if not cookie_path.exists():
        print(f"❌ Cookie文件不存在: {cookie_path}")
        print("请先运行: python get_xiaohongshu_cookie.py")
        return False
    
    try:
        # 调用统计函数
        data = await get_xiaohongshu_statistics(str(cookie_path), debug=False)
        
        if data:
            print(f"✅ 测试成功: {data}")
            return True
        else:
            print("❌ 测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_xiaohongshu_stats())