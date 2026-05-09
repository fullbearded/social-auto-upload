#!/usr/bin/env python3
"""
快手统计模块 - 与多平台工具兼容
Kuaishou Statistics Module - Compatible with multi-platform tools
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from patchright.async_api import async_playwright
from conf import LOCAL_CHROME_PATH


async def get_kuaishou_statistics(cookie_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    获取快手账号统计数据
    
    Args:
        cookie_path: Cookie文件路径
        debug: 是否启用调试模式
    
    Returns:
        统计数据字典，失败返回None
    """
    
    if not Path(LOCAL_CHROME_PATH).exists():
        print(f"❌ Chrome 浏览器未找到: {LOCAL_CHROME_PATH}")
        return None
    
    if not Path(cookie_path).exists():
        print(f"❌ Cookie 文件未找到: {cookie_path}")
        return None
    
    try:
        # 读取Cookie文件
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        
        if not cookie_data:
            print("❌ Cookie 文件为空")
            return None
        
        async with async_playwright() as p:
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
            
            browser = await p.chromium.launch(**launch_options)
            context = await browser.new_context()
            
            # 设置Cookie - 支持多种格式
            if isinstance(cookie_data, dict) and 'cookies' in cookie_data:
                # 新格式：包含cookies数组的对象
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
                        'domain': '.kuaishou.com',
                        'path': '/',
                        'expires': -1,
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'Lax'
                    })
                await context.add_cookies(playwright_cookies)
            
            page = await context.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # 访问快手个人主页或主页
            try:
                await page.goto('https://cp.kuaishou.com/profile', wait_until='networkidle')
            except:
                # 如果profile页面404，尝试访问主页
                print("⚠️  无法访问个人主页，尝试访问主页...")
                await page.goto('https://cp.kuaishou.com/profile', wait_until='networkidle')
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 检查是否登录成功
            try:
                # 先检查页面是否加载成功
                page_title = await page.title()
                print(f"📄 页面标题: {page_title}")
                
                # 检查当前URL
                current_url = page.url
                print(f"🔗 当前URL: {current_url}")
                
                # 检查是否包含登录相关内容
                if '登录' in page_title or 'login' in current_url:
                    print("❌ 检测到登录页面，Cookie可能已失效")
                    if debug:
                        print("🔍 调试模式：请手动登录后按回车键继续...")
                        await page.pause()
                    return None
                
                # 检查是否为404页面
                if '404' in page_title or '404' in current_url:
                    print("⚠️  页面返回404，但继续尝试提取数据")
                
                # 尝试找到用户信息元素（但不强制要求）
                user_elements = await page.query_selector_all('.user-info, .profile-header, .user-profile, [class*="user"], [class*="profile"]')
                if user_elements:
                    print(f"✅ 找到 {len(user_elements)} 个用户相关元素")
                else:
                    print("⚠️  未找到用户信息元素，但继续尝试提取数据")
                    
            except Exception as e:
                print(f"⚠️  登录状态检查失败: {e}")
                # 继续尝试提取数据
            
            # 获取统计数据
            stats_data = await page.evaluate('''
                () => {
                    const data = {
                        followers: 0,
                        following: 0,
                        likes: 0,
                        videos_count: 0
                    };
                    
                    // 尝试多种选择器来获取粉丝数
                    const followerSelectors = [
                        'span[data-testid="follower-count"]',
                        '.follower-count',
                        '.fans-count',
                        'a[href*="fans"] span',
                        '.user-stat .fans span'
                    ];
                    
                    // 尝试多种选择器来获取关注数
                    const followingSelectors = [
                        'span[data-testid="following-count"]',
                        '.following-count',
                        'a[href*="following"] span',
                        '.user-stat .following span'
                    ];
                    
                    // 尝试多种选择器来获取获赞数
                    const likeSelectors = [
                        'span[data-testid="like-count"]',
                        '.like-count',
                        '.like-number',
                        '.user-stat .likes span'
                    ];
                    
                    // 尝试获取视频数
                    const videoSelectors = [
                        'span[data-testid="video-count"]',
                        '.video-count',
                        '.work-count',
                        '.user-stat .works span'
                    ];
                    
                    // 获取粉丝数
                    for (const selector of followerSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            const text = element.textContent.replace(/[^0-9]/g, '');
                            if (text) {
                                data.followers = parseInt(text) || 0;
                                break;
                            }
                        }
                    }
                    
                    // 获取关注数
                    for (const selector of followingSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            const text = element.textContent.replace(/[^0-9]/g, '');
                            if (text) {
                                data.following = parseInt(text) || 0;
                                break;
                            }
                        }
                    }
                    
                    // 获取获赞数
                    for (const selector of likeSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            const text = element.textContent.replace(/[^0-9]/g, '');
                            if (text) {
                                data.likes = parseInt(text) || 0;
                                break;
                            }
                        }
                    }
                    
                    // 获取视频数
                    for (const selector of videoSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            const text = element.textContent.replace(/[^0-9]/g, '');
                            if (text) {
                                data.videos_count = parseInt(text) || 0;
                                break;
                            }
                        }
                    }
                    
                    return data;
                }
            ''')
            
            # 如果获取不到数据，尝试其他方法
            if stats_data['followers'] == 0:
                print("⚠️  使用备用方法获取数据...")
                try:
                    # 等待更长时间让页面完全加载
                    await asyncio.sleep(5)
                    
                    # 尝试通过页面文本内容提取数据
                    page_text = await page.text_content('body')
                    if page_text:
                        import re
                        
                        # 尝试匹配粉丝数
                        fans_match = re.search(r'粉丝[：:\s]*([0-9,]+)', page_text)
                        if fans_match:
                            stats_data['followers'] = int(fans_match.group(1).replace(',', ''))
                        
                        # 尝试匹配关注数
                        follow_match = re.search(r'关注[：:\s]*([0-9,]+)', page_text)
                        if follow_match:
                            stats_data['following'] = int(follow_match.group(1).replace(',', ''))
                        
                        # 尝试匹配获赞数
                        like_match = re.search(r'获赞[：:\s]*([0-9,]+)', page_text)
                        if like_match:
                            stats_data['likes'] = int(like_match.group(1).replace(',', ''))
                        
                        # 尝试匹配作品数
                        work_match = re.search(r'作品[：:\s]*([0-9,]+)', page_text)
                        if work_match:
                            stats_data['videos_count'] = int(work_match.group(1).replace(',', ''))
                except Exception as e:
                    print(f"⚠️  备用方法失败: {e}")
            
            # 添加时间戳
            from datetime import datetime
            stats_data['timestamp'] = datetime.now().isoformat()
            stats_data['platform'] = 'kuaishou'
            
            # 验证数据
            if stats_data['followers'] == 0 and stats_data['following'] == 0:
                print("⚠️  获取到的数据可能不完整")
                if debug:
                    print("🔍 调试模式：请检查页面显示是否正常")
                    print("🔍 按回车键继续...")
                    try:
                        await page.pause()
                    except:
                        pass
                # 在调试模式下，即使数据不完整也返回，让用户决定
                return stats_data
            else:
                print(f"✅ 成功获取快手数据: 粉丝{stats_data['followers']:,} 关注{stats_data['following']:,} 获赞{stats_data['likes']:,}")
            
            if not debug:
                await browser.close()
            else:
                print("🔍 调试模式：浏览器保持打开状态")
            
            return stats_data
            
    except json.JSONDecodeError as e:
        print(f"❌ Cookie 文件格式错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 获取 kuaishou 统计数据时出错: {e}")
        if debug:
            print("🔍 调试模式已启用，浏览器将保持打开状态以便调试")
            print("请在浏览器中检查问题，然后按回车键继续...")
            import traceback
            traceback.print_exc()
            # 尝试保持浏览器打开以便调试
            try:
                if 'browser' in locals() and browser:
                    # 创建一个新页面用于暂停
                    page = await browser.new_page()
                    await page.goto("about:blank")
                    await page.pause()
            except:
                pass
        return None


# 测试函数
async def test_kuaishou_stats():
    """测试快手统计功能"""
    print("🧪 测试快手统计功能...")
    
    # 检查Cookie文件
    cookie_path = Path("cookies/ks_uploader/account.json")
    if not cookie_path.exists():
        print(f"❌ Cookie文件不存在: {cookie_path}")
        return False
    
    # 调用统计函数
    result = await get_kuaishou_statistics(str(cookie_path), debug=False)
    
    if result:
        print(f"✅ 测试成功: {result}")
        return True
    else:
        print("❌ 测试失败")
        return False


if __name__ == "__main__":
    asyncio.run(test_kuaishou_stats())