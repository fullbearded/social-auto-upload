#!/usr/bin/env python3
"""
腾讯视频号数据统计模块
获取视频号账号的粉丝、关注、获赞等数据
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import tencent_logger


class TencentStatsError(Exception):
    """腾讯视频号统计异常"""
    pass


async def get_tencent_statistics(cookie_path: str, debug: bool = False) -> Dict[str, Any]:
    """
    获取腾讯视频号统计数据
    
    Args:
        cookie_path: Cookie文件路径
        debug: 是否启用调试模式（浏览器不自动关闭）
    
    Returns:
        包含统计数据的字典
    """
    if not Path(cookie_path).exists():
        raise TencentStatsError(f"Cookie文件不存在: {cookie_path}")
    
    if not Path(LOCAL_CHROME_PATH).exists():
        raise TencentStatsError(f"Chrome浏览器未找到: {LOCAL_CHROME_PATH}")
    
    browser = None
    try:
        async with async_playwright() as playwright:
            # 启动浏览器
            if debug:
                # 调试模式：显示浏览器
                launch_options = {
                    'headless': False,
                    'executable_path': LOCAL_CHROME_PATH,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                }
            else:
                # 正常模式：使用新headless
                launch_options = {
                    'headless': True,
                    'executable_path': LOCAL_CHROME_PATH,
                    'args': [
                        '--headless=new',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                }
            browser = await playwright.chromium.launch(**launch_options)
            
            # 创建上下文并加载cookie
            context = await browser.new_context(storage_state=cookie_path)
            context = await set_init_script(context)
            page = await context.new_page()
            
            # 访问视频号平台数据页面
            await page.goto("https://channels.weixin.qq.com/platform")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # 等待页面完全加载
            
            # 检查是否登录成功
            if "login" in page.url or await page.locator('text="登录"').count() > 0:
                raise TencentStatsError("Cookie已失效，需要重新登录")
            
            # 获取统计数据
            stats_data = await _extract_stats_data(page)
            
            # 如果是调试模式，暂停执行
            if debug:
                tencent_logger.info("🔍 调试模式：浏览器将保持打开状态")
                tencent_logger.info("请在浏览器中检查数据，然后按回车键继续...")
                await page.pause()
            
            return stats_data
            
    except Exception as e:
        raise TencentStatsError(f"获取腾讯视频号统计数据失败: {e}")
    finally:
        # 非调试模式下关闭浏览器
        if browser and not debug:
            await browser.close()


async def _extract_stats_data(page: Page) -> Dict[str, Any]:
    """从页面提取统计数据"""
    stats_data = {
        'platform': 'tencent',
        'account_name': '',
        'followers': 0,
        'following': 0,
        'likes': 0,
        'videos_count': 0,
        'timestamp': datetime.now().isoformat(),
        'raw_data': {},
        'daily_stats': {}  # 添加昨日统计数据
    }
    
    try:
        # 获取账号名称
        try:
            name_selectors = [
                '.user-name',
                '.nickname',
                '.account-name',
                '[class*="name"]'
            ]
            
            for selector in name_selectors:
                element = page.locator(selector)
                if await element.count() > 0:
                    name_text = await element.first.text_content()
                    if name_text and name_text.strip():
                        stats_data['account_name'] = name_text.strip()
                        break
        except Exception as e:
            tencent_logger.warning(f"获取账号名称失败: {e}")
        
        # 使用新的页面结构提取数据
        await _extract_tencent_platform_data(page, stats_data)
        
        stats_data['raw_data']['url'] = page.url
        
    except Exception as e:
        tencent_logger.error(f"提取统计数据时出错: {e}")
    
    return stats_data


async def _parse_stat_elements(elements, stats_data: Dict[str, Any]):
    """解析统计元素"""
    try:
        for i in range(await elements.count()):
            element = elements.nth(i)
            text = await element.text_content()
            
            if not text or not text.strip():
                continue
                
            text = text.strip()
            
            # 使用正则表达式提取数字和标签
            # 支持格式： "1.2万粉丝", "12345关注", "6.7k获赞" 等
            patterns = [
                r'(\d+(?:\.\d+)?)\s*(万|w|k)\s*(粉丝|关注者|follower)s?',
                r'(\d+)\s*(粉丝|关注者|followers)',
                r'(\d+(?:\.\d+)?)\s*(万|w|k)\s*(关注|following)',
                r'(\d+)\s*(关注|following)',
                r'(\d+(?:\.\d+)?)\s*(万|w|k)\s*(获赞|喜欢|赞|like)s?',
                r'(\d+)\s*(获赞|喜欢|赞|likes)',
                r'(\d+(?:\.\d+)?)\s*(万|w|k)\s*(视频|作品|video)s?',
                r'(\d+)\s*(视频|作品|videos)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        number = match[0]
                        unit = match[1].lower() if len(match) > 2 else ''
                        label = match[-1].lower()
                        
                        # 转换单位
                        value = float(number)
                        if unit in ['万', 'w']:
                            value *= 10000
                        elif unit in ['k']:
                            value *= 1000
                        
                        value = int(value)
                        
                        # 根据标签分类
                        if '粉丝' in label or 'follower' in label:
                            stats_data['followers'] = value
                        elif '关注' in label or 'following' in label:
                            stats_data['following'] = value
                        elif '赞' in label or 'like' in label:
                            stats_data['likes'] = value
                        elif '视频' in label or 'video' in label or '作品' in label:
                            stats_data['videos_count'] = value
                            
    except Exception as e:
        tencent_logger.warning(f"解析统计元素失败: {e}")


async def _parse_current_page_stats(page: Page, stats_data: Dict[str, Any]):
    """解析当前页面的统计数据"""
    try:
        # 查找可能的统计数据区域
        page_text = await page.text_content('body')
        if page_text:
            # 使用正则表达式从页面文本中提取数据
            text_patterns = [
                (r'粉丝[：:\s]*(\d+(?:\.\d+)?[万wk]?)', 'followers'),
                (r'关注[：:\s]*(\d+(?:\.\d+)?[万wk]?)', 'following'),
                (r'获赞[：:\s]*(\d+(?:\.\d+)?[万wk]?)', 'likes'),
                (r'视频[：:\s]*(\d+(?:\.\d+)?[万wk]?)', 'videos_count'),
                (r'作品[：:\s]*(\d+(?:\.\d+)?[万wk]?)', 'videos_count')
            ]
            
            for pattern, key in text_patterns:
                matches = re.search(pattern, page_text, re.IGNORECASE)
                if matches:
                    value_str = matches.group(1)
                    value = _parse_number(value_str)
                    if value:
                        stats_data[key] = value
                        stats_data['raw_data'][f'{key}_source'] = 'page_text'
                        
    except Exception as e:
        tencent_logger.warning(f"解析当前页面统计失败: {e}")


async def _try_api_data_fetch(page: Page, stats_data: Dict[str, Any]):
    """尝试通过API获取数据"""
    try:
        # 监听网络请求
        api_data = {}
        
        def handle_response(response):
            try:
                if 'api' in response.url.lower() and 'stat' in response.url.lower():
                    api_data[response.url] = response.json()
            except:
                pass
        
        page.on('response', handle_response)
        
        # 刷新页面或点击某些元素以触发API请求
        await page.reload()
        await asyncio.sleep(3)
        
        # 分析获取到的API数据
        for url, data in api_data.items():
            if isinstance(data, dict):
                stats_data['raw_data']['api_data'] = data
                # 尝试从API数据中提取统计信息
                await _extract_from_api_data(data, stats_data)
                
    except Exception as e:
        tencent_logger.warning(f"API数据获取失败: {e}")


async def _extract_from_api_data(api_data: Dict, stats_data: Dict[str, Any]):
    """从API数据中提取统计信息"""
    try:
        # 递归查找可能的统计数据
        def find_stats_values(obj, keys=['fans', 'follower', 'follow', 'like', 'view', 'video']):
            values = {}
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_lower = key.lower()
                    for target_key in keys:
                        if target_key in key_lower:
                            if isinstance(value, (int, float)):
                                values[target_key] = int(value)
                            elif isinstance(value, str) and value.isdigit():
                                values[target_key] = int(value)
                    # 递归查找
                    nested_values = find_stats_values(value, keys)
                    values.update(nested_values)
            elif isinstance(obj, list):
                for item in obj:
                    nested_values = find_stats_values(item, keys)
                    values.update(nested_values)
            return values
        
        found_values = find_stats_values(api_data)
        
        # 映射找到的值到统计字段
        mapping = {
            'fan': 'followers',
            'follower': 'followers',
            'follow': 'following',
            'like': 'likes',
            'video': 'videos_count'
        }
        
        for found_key, value in found_values.items():
            for map_key, stat_key in mapping.items():
                if map_key in found_key and not stats_data.get(stat_key):
                    stats_data[stat_key] = value
                    
    except Exception as e:
        tencent_logger.warning(f"从API数据提取失败: {e}")


def _parse_number(number_str: str) -> Optional[int]:
    """解析数字字符串"""
    try:
        number_str = number_str.strip().lower()
        
        # 处理带单位的数字
        if '万' in number_str or 'w' in number_str:
            number = float(number_str.replace('万', '').replace('w', ''))
            return int(number * 10000)
        elif 'k' in number_str:
            number = float(number_str.replace('k', ''))
            return int(number * 1000)
        else:
            return int(float(number_str))
    except:
        return None


class TencentStatsUploader:
    """腾讯视频号统计上传器"""
    
    def __init__(self, cookie_path: str, debug: bool = False):
        self.cookie_path = cookie_path
        self.debug = debug
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        return await get_tencent_statistics(self.cookie_path, self.debug)


# 兼容性别名
TencentWeixinStatsUploader = TencentStatsUploader


async def get_tencent_weixin_statistics(cookie_path: str, debug: bool = False) -> Dict[str, Any]:
    """获取腾讯视频号统计数据的别名函数"""
    return await get_tencent_statistics(cookie_path, debug)


if __name__ == "__main__":
    async def test():
        """测试函数"""
        cookie_path = "cookies/tencent_uploader/account.json"
        
        if not Path(cookie_path).exists():
            print(f"❌ Cookie文件不存在: {cookie_path}")
            return
        
        try:
            print("🚀 开始获取腾讯视频号统计数据...")
            data = await get_tencent_statistics(cookie_path, debug=True)
            
            print(f"\n📊 腾讯视频号统计数据:")
            print(f"   账号名称: {data.get('account_name', '未知')}")
            print(f"   粉丝数: {data.get('followers', 0):,}")
            print(f"   关注数: {data.get('following', 0):,}")
            print(f"   获赞数: {data.get('likes', 0):,}")
            print(f"   视频数: {data.get('videos_count', 0):,}")
            print(f"   获取时间: {data.get('timestamp', '未知')}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    asyncio.run(test())


async def _extract_tencent_platform_data(page: Page, stats_data: Dict[str, Any]):
    """从腾讯视频号平台页面提取数据（基于新的页面结构）"""
    try:
        tencent_logger.info("开始提取腾讯视频号平台数据...")
        
        # 等待页面加载完成
        await page.wait_for_selector('.finder-content-info', timeout=10000)
        await asyncio.sleep(2)
        
        # 提取主要统计数据（视频数和关注者数）
        try:
            # 使用页面评估来提取数据
            main_stats = await page.evaluate('''
                () => {
                    const result = {
                        videos: 0,
                        followers: 0
                    };
                    
                    // 查找 .finder-content-info 区域
                    const contentInfo = document.querySelector('.finder-content-info');
                    if (contentInfo) {
                        // 查找所有包含数字的元素
                        const numberElements = contentInfo.querySelectorAll('.finder-info-num');
                        const labels = contentInfo.querySelectorAll('span:not(.finder-info-num)');
                        
                        // 提取标签文本
                        const labelTexts = Array.from(labels).map(el => el.textContent.trim());
                        const numberTexts = Array.from(numberElements).map(el => el.textContent.trim());
                        
                        // 根据标签匹配数据
                        labelTexts.forEach((label, index) => {
                            if (label.includes('视频') && numberTexts[index]) {
                                result.videos = _parseNumber(numberTexts[index]);
                            } else if (label.includes('关注者') && numberTexts[index]) {
                                result.followers = _parseNumber(numberTexts[index]);
                            }
                        });
                    }
                    
                    return result;
                }
                
                function _parseNumber(text) {
                    if (!text) return 0;
                    
                    // 处理中文数字格式
                    text = text.replace(/[^\d.万kK]/g, '');
                    
                    if (text.includes('万') || text.includes('w') || text.includes('W')) {
                        return parseFloat(text.replace(/[万wW]/g, '')) * 10000;
                    } else if (text.includes('k') || text.includes('K')) {
                        return parseFloat(text.replace(/[kK]/g, '')) * 1000;
                    }
                    
                    return parseFloat(text) || 0;
                }
            ''')
            
            stats_data['videos_count'] = main_stats.get('videos', 0)
            stats_data['followers'] = main_stats.get('followers', 0)
            
            tencent_logger.info(f"主要数据提取成功: 视频 {stats_data['videos_count']}, 粉丝 {stats_data['followers']}")
            
        except Exception as e:
            tencent_logger.warning(f"提取主要统计数据失败: {e}")
        
        # 提取昨日数据
        try:
            daily_stats = await page.evaluate('''
                () => {
                    const result = {
                        new_followers: 0,
                        new_plays: 0,
                        new_likes: 0,
                        new_comments: 0
                    };
                    
                    // 查找昨日数据区域
                    const adminArea = document.querySelector('.admin-area');
                    if (adminArea) {
                        const dataItems = adminArea.querySelectorAll('.data-item');
                        
                        dataItems.forEach(item => {
                            const nameElement = item.querySelector('.data-name');
                            const valueElement = item.querySelector('.data');
                            
                            if (nameElement && valueElement) {
                                const name = nameElement.textContent.trim();
                                const value = valueElement.textContent.trim();
                                
                                if (name.includes('净增关注')) {
                                    result.new_followers = _parseNumber(value);
                                } else if (name.includes('新增播放')) {
                                    result.new_plays = _parseNumber(value);
                                } else if (name.includes('新增') && name.includes('❤')) {
                                    result.new_likes = _parseNumber(value);
                                } else if (name.includes('新增评论')) {
                                    result.new_comments = _parseNumber(value);
                                }
                            }
                        });
                    }
                    
                    return result;
                }
                
                function _parseNumber(text) {
                    if (!text) return 0;
                    
                    // 处理中文数字格式
                    text = text.replace(/[^\d.万kK]/g, '');
                    
                    if (text.includes('万') || text.includes('w') || text.includes('W')) {
                        return parseFloat(text.replace(/[万wW]/g, '')) * 10000;
                    } else if (text.includes('k') || text.includes('K')) {
                        return parseFloat(text.replace(/[kK]/g, '')) * 1000;
                    }
                    
                    return parseFloat(text) || 0;
                }
            ''')
            
            stats_data['daily_stats'] = daily_stats
            stats_data['raw_data']['daily_stats'] = daily_stats
            
            tencent_logger.info(f"昨日数据提取成功: {daily_stats}")
            
        except Exception as e:
            tencent_logger.warning(f"提取昨日数据失败: {e}")
        
        # 如果没有获取到关注数，尝试其他方法
        if stats_data['followers'] == 0:
            try:
                # 尝试从其他可能的位置获取粉丝数
                fallback_data = await page.evaluate('''
                    () => {
                        // 尝试各种可能的选择器
                        const selectors = [
                            '.followers-count',
                            '.fans-count', 
                            '[class*="follower"]',
                            '[class*="fans"]',
                            'text*="粉丝"',
                            'text*="关注者"'
                        ];
                        
                        for (const selector of selectors) {
                            const elements = document.querySelectorAll(selector);
                            for (const el of elements) {
                                const text = el.textContent || '';
                                const match = text.match(/(\d+(?:\.\d+)?[万kK]?)/);
                                if (match) {
                                    return _parseNumber(match[1]);
                                }
                            }
                        }
                        
                        return 0;
                    }
                    
                    function _parseNumber(text) {
                        if (!text) return 0;
                        text = text.replace(/[^\d.万kK]/g, '');
                        
                        if (text.includes('万') || text.includes('w') || text.includes('W')) {
                            return parseFloat(text.replace(/[万wW]/g, '')) * 10000;
                        } else if (text.includes('k') || text.includes('K')) {
                            return parseFloat(text.replace(/[kK]/g, '')) * 1000;
                        }
                        
                        return parseFloat(text) || 0;
                    }
                ''')
                
                if fallback_data > 0:
                    stats_data['followers'] = fallback_data
                    tencent_logger.info(f"使用备用方法获取粉丝数: {fallback_data}")
                    
            except Exception as e:
                tencent_logger.warning(f"备用方法获取粉丝数失败: {e}")
        
        # 计算总获赞数（如果没有直接获取到）
        if stats_data['likes'] == 0:
            # 这里可以尝试从其他页面或API获取获赞数
            # 目前设置为0，等待后续扩展
            stats_data['likes'] = 0
        
        # 设置关注数（腾讯视频号主要是粉丝数，不是传统意义上的关注数）
        stats_data['following'] = 0
        
        tencent_logger.info(f"最终统计数据: {stats_data}")
        
    except Exception as e:
        tencent_logger.error(f"提取腾讯平台数据失败: {e}")
        import traceback
        traceback.print_exc()