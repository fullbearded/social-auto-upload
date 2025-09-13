#!/usr/bin/env python3
"""
快手粉丝数据获取工具 - 一键使用
快速获取快手账号粉丝数据
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# 保持兼容性
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from conf import LOCAL_CHROME_PATH

# 检查 Chrome 路径
if not LOCAL_CHROME_PATH or not Path(LOCAL_CHROME_PATH).exists():
    print("⚠️  Chrome 路径未配置或不存在")
    print("请检查 conf.py 中的 LOCAL_CHROME_PATH 设置")
    # 尝试常见路径
    common_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    ]
    for path in common_paths:
        if Path(path).exists():
            print(f"发现 Chrome: {path}")
            print(f"请更新 conf.py 中的 LOCAL_CHROME_PATH = \"{path}\"")
            break

async def get_followers_only(cookie_path: str) -> dict:
    """只获取快手粉丝数据"""
    
    if not Path(LOCAL_CHROME_PATH).exists():
        raise FileNotFoundError(f"Chrome 浏览器未找到: {LOCAL_CHROME_PATH}")
    
    if not Path(cookie_path).exists():
        raise FileNotFoundError(f"Cookie 文件未找到: {cookie_path}")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            executable_path=LOCAL_CHROME_PATH
        )
        
        try:
            # 创建上下文并加载cookie
            context = await browser.new_context(storage_state=cookie_path)
            page = await context.new_page()
            
            # 访问个人主页
            await page.goto("https://cp.kuaishou.com/profile")
            await page.wait_for_load_state("networkidle")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 点击头像获取详细信息
            avatar_selector = 'div.user-info-name'
            if await page.locator(avatar_selector).count() > 0:
                await page.locator(avatar_selector).click()
                await asyncio.sleep(2)
            
            # 获取粉丝数据
            followers_data = {}
            
            # 尝试从页面结构获取粉丝数
            user_cnt_selector = 'div.user-cnt__item'
            user_cnt_items = await page.locator(user_cnt_selector).all()
            
            for item in user_cnt_items:
                try:
                    # 获取所有文本内容
                    full_text = await item.text_content()
                    
                    # 提取数字和标签
                    # 格式通常是 "25粉丝" 或 "21关注"
                    import re
                    match = re.search(r'(\d+)(.+)', full_text.strip())
                    if match:
                        number = match.group(1)
                        label = match.group(2).strip()
                        
                        if '粉丝' in label:
                            followers_data['followers'] = int(number)
                        elif '关注' in label:
                            followers_data['following'] = int(number)
                        elif '获赞' in label:
                            followers_data['likes'] = int(number)
                        
                except Exception as e:
                    print(f"解析用户数据项失败: {e}")
                    continue
            
            # 获取账号名称
            try:
                account_name = await page.locator('.user-info-name').text_content()
                followers_data['account_name'] = account_name.strip() if account_name else "未知"
            except:
                followers_data['account_name'] = "未知"
            
            return followers_data
            
        except Exception as e:
            print(f"获取粉丝数据失败: {e}")
            return {}
        finally:
            await browser.close()

async def main():
    """演示快速获取快手粉丝数据"""
    print("🚀 快手粉丝数据获取工具")
    print("=" * 50)
    
    # 设置cookie路径
    cookie_path = Path(__file__).parent / "cookies" / "ks_uploader" / "account.json"
    
    if not cookie_path.exists():
        print("❌ 未找到快手Cookie文件")
        print("请确保在以下路径有文件:")
        print(f"   {cookie_path}")
        print("可通过运行 python examples/get_ks_cookie.py 获取Cookie")
        return
    
    print(f"✅ 找到Cookie文件: {cookie_path}")
    
    try:
        # 获取粉丝数据
        print("🔄 正在获取快手粉丝数据...")
        data = await get_followers_only(str(cookie_path))
        
        if not data:
            print("❌ 粉丝数据获取失败")
            return
        
        # 显示粉丝数据
        print(f"\n📊 快手账号粉丝数据:")
        print(f"   账号名称: {data.get('account_name', '未知')}")
        print(f"   粉丝数: {data.get('followers', 0):,}")
        print(f"   关注数: {data.get('following', 0):,}")
        print(f"   获赞数: {data.get('likes', 0):,}")
        
        print("\n✅ 粉丝数据获取完成!")
        
    except Exception as e:
        print(f"💥 运行错误: {e}")
        print("🔍 请检查网络连接和Cookie有效性")


if __name__ == "__main__":
    asyncio.run(main())