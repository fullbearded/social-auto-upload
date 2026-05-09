#!/usr/bin/env python3
"""
腾讯视频号封面预览状态检查工具 - 兼容Windows和Mac平台
Tencent Video Channel Cover Preview Status Checker - Cross-platform Compatible
"""

import asyncio
import sys
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from patchright.async_api import Page, Locator

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.log import tencent_logger


class CoverPreviewChecker:
    """封面预览状态检查器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.platform_system = platform.system().lower()
        self.is_windows = self.platform_system == 'windows'
        self.is_mac = self.platform_system == 'darwin'
        
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'system': self.platform_system,
            'is_windows': self.is_windows,
            'is_mac': self.is_mac,
            'platform_name': 'Windows' if self.is_windows else 'Mac' if self.is_mac else 'Unknown'
        }
    
    async def check_cover_preview_ready(self) -> Tuple[bool, str, Optional[Locator]]:
        """
        检查封面预览是否准备就绪
        
        Returns:
            Tuple[bool, str, Optional[Locator]]: 
                - 是否准备就绪
                - 状态描述
                - 可点击的元素（如果存在）
        """
        platform_info = self.get_platform_info()
        tencent_logger.info(f"检查封面预览状态 - 平台: {platform_info['platform_name']}")
        
        try:
            # 首先检查封面预览区域是否存在
            cover_preview_area = await self._find_cover_preview_area()
            if not cover_preview_area:
                return False, "未找到封面预览区域", None
            
            tencent_logger.info("✓ 找到封面预览区域")
            
            # 根据平台使用不同的检查策略
            if self.is_windows:
                return await self._check_windows_cover_ready(cover_preview_area)
            elif self.is_mac:
                return await self._check_mac_cover_ready(cover_preview_area)
            else:
                # 未知平台，尝试两种方法
                tencent_logger.warning("未知平台，尝试所有检查方法")
                return await self._check_unknown_platform_cover_ready(cover_preview_area)
                
        except Exception as e:
            tencent_logger.error(f"检查封面预览状态时出错: {e}")
            return False, f"检查过程出错: {e}", None
    
    async def _find_cover_preview_area(self) -> Optional[Locator]:
        """查找封面预览区域"""
        try:
            # 尝试多种可能的选择器来找到封面预览区域
            selectors = [
                "div.label:has-text('封面预览')",
                "div.cover-preview-wrap", 
                "div.vertical-cover-wrap",
                "div.img-popover-wrap",
                "div.finder-tag-wrap",
                "[class*='cover-preview']",
                "[class*='thumbnail-preview']"
            ]
            
            for selector in selectors:
                element = self.page.locator(selector)
                if await element.count() > 0:
                    tencent_logger.info(f"找到封面预览区域: {selector}")
                    return element
            
            tencent_logger.warning("未找到封面预览区域")
            return None
            
        except Exception as e:
            tencent_logger.error(f"查找封面预览区域时出错: {e}")
            return None
    
    async def _check_windows_cover_ready(self, cover_area: Locator) -> Tuple[bool, str, Optional[Locator]]:
        """检查Windows平台封面预览状态"""
        tencent_logger.info("使用Windows平台检查策略")
        
        try:
            # Windows平台：查找"更换封面"按钮
            change_cover_button = None
            
            # 方法1：通过提供的HTML结构查找
            windows_selectors = [
                "span.weui-desktop-popover__target div.finder-tag-wrap.btn div.tag-inner:has-text('更换封面')",
                "div.finder-tag-wrap.btn div.tag-inner:has-text('更换封面')",
                "span.weui-desktop-popover__target div.finder-tag-wrap",
                "div.tag-inner:has-text('更换封面')",
                "div.btn:has-text('更换封面')",
                "div.finder-tag-wrap:has-text('更换封面')",
                "button:has-text('更换封面')",
                "[class*='cover-change']:has-text('更换')",
                "[class*='cover-change']:has-text('封面')"
            ]
            
            for selector in windows_selectors:
                element = self.page.locator(selector)
                if await element.count() > 0:
                    change_cover_button = element.first
                    break
            
            if change_cover_button:
                # 检查按钮是否可点击
                is_visible = await change_cover_button.is_visible()
                is_enabled = await change_cover_button.is_enabled()
                
                if is_visible and is_enabled:
                    tencent_logger.info("✓ Windows平台：更换封面按钮可点击")
                    return True, "Windows平台：更换封面按钮已准备就绪", change_cover_button
                else:
                    reason = "不可见" if not is_visible else "不可点击"
                    tencent_logger.info(f"⚠ Windows平台：更换封面按钮{reason}")
                    return False, f"Windows平台：更换封面按钮{reason}", change_cover_button
            else:
                tencent_logger.warning("⚠ Windows平台：未找到更换封面按钮")
                return False, "Windows平台：未找到更换封面按钮", None
                
        except Exception as e:
            tencent_logger.error(f"Windows平台检查失败: {e}")
            return False, f"Windows平台检查失败: {e}", None
    
    async def _check_mac_cover_ready(self, cover_area: Locator) -> Tuple[bool, str, Optional[Locator]]:
        """检查Mac平台封面预览状态"""
        tencent_logger.info("使用Mac平台检查策略")
        
        try:
            # Mac平台：查找"编辑"按钮
            edit_button = None
            
            # 方法1：查找编辑按钮
            mac_selectors = [
                "div.cover-preview-wrap div:has-text('编辑')",
                "div.edit-btn",
                "div.edit-btn-zIndex", 
                "button:has-text('编辑')",
                "div.btn:has-text('编辑')",
                "div.tag-inner:has-text('编辑')",
                "[class*='edit']:has-text('编辑')",
                "[class*='edit-btn']"
            ]
            
            for selector in mac_selectors:
                element = self.page.locator(selector)
                if await element.count() > 0:
                    edit_button = element.first
                    break
            
            if edit_button:
                # 检查按钮是否可点击
                is_visible = await edit_button.is_visible()
                is_enabled = await edit_button.is_enabled()
                
                if is_visible and is_enabled:
                    tencent_logger.info("✓ Mac平台：编辑按钮可点击")
                    return True, "Mac平台：编辑按钮已准备就绪", edit_button
                else:
                    reason = "不可见" if not is_visible else "不可点击"
                    tencent_logger.info(f"⚠ Mac平台：编辑按钮{reason}")
                    return False, f"Mac平台：编辑按钮{reason}", edit_button
            else:
                tencent_logger.warning("⚠ Mac平台：未找到编辑按钮")
                return False, "Mac平台：未找到编辑按钮", None
                
        except Exception as e:
            tencent_logger.error(f"Mac平台检查失败: {e}")
            return False, f"Mac平台检查失败: {e}", None
    
    async def _check_unknown_platform_cover_ready(self, cover_area: Locator) -> Tuple[bool, str, Optional[Locator]]:
        """检查未知平台封面预览状态"""
        tencent_logger.info("使用未知平台检查策略（尝试所有方法）")
        
        try:
            # 尝试Windows方法
            windows_ready, windows_msg, windows_button = await self._check_windows_cover_ready(cover_area)
            if windows_ready:
                return windows_ready, windows_msg, windows_button
            
            # 尝试Mac方法
            mac_ready, mac_msg, mac_button = await self._check_mac_cover_ready(cover_area)
            if mac_ready:
                return mac_ready, mac_msg, mac_button
            
            # 如果两种方法都不行，尝试通用方法
            return await self._check_generic_cover_ready(cover_area)
            
        except Exception as e:
            tencent_logger.error(f"未知平台检查失败: {e}")
            return False, f"未知平台检查失败: {e}", None
    
    async def _check_generic_cover_ready(self, cover_area: Locator) -> Tuple[bool, str, Optional[Locator]]:
        """通用封面预览检查方法"""
        tencent_logger.info("使用通用检查策略")
        
        try:
            # 查找任何可能的操作按钮
            generic_selectors = [
                "div.tag-inner",
                "div.btn", 
                "button",
                "[class*='btn']",
                "[class*='button']",
                "[class*='action']",
                "[class*='operate']"
            ]
            
            for selector in generic_selectors:
                elements = self.page.locator(selector)
                if await elements.count() > 0:
                    for i in range(await elements.count()):
                        element = elements.nth(i)
                        if await element.is_visible() and await element.is_enabled():
                            text = await element.text_content() or ""
                            if any(keyword in text for keyword in ['更换', '编辑', '修改', '设置', '选择', '更改']):
                                tencent_logger.info(f"✓ 找到可操作按钮: {text}")
                                return True, f"通用方法：找到可操作按钮 '{text}'", element
            
            tencent_logger.warning("⚠ 通用方法：未找到可操作按钮")
            return False, "通用方法：未找到可操作按钮", None
            
        except Exception as e:
            tencent_logger.error(f"通用检查失败: {e}")
            return False, f"通用检查失败: {e}", None
    
    async def wait_for_cover_preview_ready(self, timeout: int = 30, check_interval: float = 1.0) -> Tuple[bool, str, Optional[Locator]]:
        """
        等待封面预览准备就绪
        
        Args:
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            Tuple[bool, str, Optional[Locator]]: 
                - 是否成功
                - 状态描述
                - 可点击的元素（如果存在）
        """
        tencent_logger.info(f"等待封面预览准备就绪，超时时间: {timeout}秒")
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                is_ready, message, clickable_element = await self.check_cover_preview_ready()
                
                if is_ready:
                    tencent_logger.success(f"封面预览准备就绪: {message}")
                    return True, message, clickable_element
                
                # 记录当前状态但不频繁输出
                current_time = time.time() - start_time
                if int(current_time) % 5 == 0:  # 每5秒输出一次
                    tencent_logger.info(f"等待中... ({int(current_time)}/{timeout}秒) - {message}")
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                tencent_logger.error(f"检查过程中出错: {e}")
                await asyncio.sleep(check_interval)
        
        # 超时
        tencent_logger.error(f"等待封面预览准备就绪超时（{timeout}秒）")
        return False, f"等待超时（{timeout}秒）", None
    
    async def trigger_cover_change_dialog(self) -> bool:
        """
        触发封面更换弹窗
        
        Returns:
            bool: 是否成功触发
        """
        tencent_logger.info("尝试触发封面更换弹窗")
        
        try:
            # 检查封面预览状态
            is_ready, message, clickable_element = await self.check_cover_preview_ready()
            
            if not is_ready or not clickable_element:
                tencent_logger.warning(f"封面预览未准备就绪: {message}")
                return False
            
            # 点击元素
            await clickable_element.click()
            tencent_logger.info("✓ 已点击封面操作按钮")
            
            # 等待弹窗出现
            platform_info = self.get_platform_info()
            await asyncio.sleep(2)  # 等待弹窗出现
            
            # 检查弹窗是否出现
            dialog_selectors = [
                "div.cover-set-wrap",
                "div.weui-desktop-dialog",
                "div.modal",
                "div.dialog",
                "[class*='dialog']",
                "[class*='modal']"
            ]
            
            for selector in dialog_selectors:
                dialog = self.page.locator(selector)
                if await dialog.count() > 0 and await dialog.is_visible():
                    tencent_logger.success(f"✓ 封面更换弹窗已出现 ({selector})")
                    return True
            
            tencent_logger.warning("未检测到弹窗，但可能已触发")
            return True
            
        except Exception as e:
            tencent_logger.error(f"触发封面更换弹窗失败: {e}")
            return False
    
    async def get_cover_preview_status(self) -> Dict[str, Any]:
        """
        获取封面预览的完整状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        platform_info = self.get_platform_info()
        
        try:
            # 基础状态检查
            is_ready, message, clickable_element = await self.check_cover_preview_ready()
            
            result = {
                'platform': platform_info,
                'is_ready': is_ready,
                'message': message,
                'has_clickable_element': clickable_element is not None,
                'clickable_element_selector': None,
                'clickable_element_text': None,
                'cover_area_found': False,
                'page_url': self.page.url,
                'page_title': await self.page.title()
            }
            
            # 如果找到可点击元素，获取详细信息
            if clickable_element:
                try:
                    # 尝试获取选择器
                    element_handle = await clickable_element.element_handle()
                    if element_handle:
                        # 获取元素的XPath或CSS选择器
                        result['clickable_element_selector'] = await self._get_element_selector(element_handle)
                        result['clickable_element_text'] = await clickable_element.text_content()
                except:
                    pass
            
            # 检查封面预览区域
            cover_area = await self._find_cover_preview_area()
            result['cover_area_found'] = cover_area is not None
            
            return result
            
        except Exception as e:
            return {
                'platform': platform_info,
                'is_ready': False,
                'message': f'获取状态时出错: {e}',
                'has_clickable_element': False,
                'clickable_element_selector': None,
                'clickable_element_text': None,
                'cover_area_found': False,
                'page_url': self.page.url,
                'page_title': await self.page.title(),
                'error': str(e)
            }
    
    async def _get_element_selector(self, element_handle) -> Optional[str]:
        """获取元素的选择器"""
        try:
            # 在页面中注入XPath和CSS路径获取函数
            js_functions = '''
            function getXPath(element) {
                if (element.id !== '') {
                    return 'id("' + element.id + '")';
                }
                if (element === document.body) {
                    return element.tagName;
                }
                
                var ix = 0;
                var siblings = element.parentNode.childNodes;
                for (var i = 0; i < siblings.length; i++) {
                    var sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            function getCssPath(element) {
                if (element.id) {
                    return '#' + element.id;
                }
                if (element.className) {
                    var classes = element.className.split(' ').filter(c => c.trim());
                    if (classes.length > 0) {
                        return element.tagName.toLowerCase() + '.' + classes.join('.');
                    }
                }
                
                var path = [];
                while (element.nodeType === Node.ELEMENT_NODE) {
                    var selector = element.tagName.toLowerCase();
                    if (element.id) {
                        selector = '#' + element.id;
                        path.unshift(selector);
                        break;
                    } else if (element.className) {
                        selector += '.' + element.className.trim().split(/\\s+/).join('.');
                    }
                    
                    var siblings = element.parentNode.children;
                    var index = Array.from(siblings).indexOf(element) + 1;
                    if (siblings.length > 1 && index > 1) {
                        selector += ':nth-child(' + index + ')';
                    }
                    
                    path.unshift(selector);
                    element = element.parentNode;
                }
                
                return path.join(' > ');
            }
            '''
            
            # 尝试获取元素的XPath
            xpath = await element_handle.evaluate(f'element => {{ {js_functions} return getXPath(element); }}')
            if xpath and xpath != '/HTML[1]/BODY[1]':
                return xpath
        except:
            pass
        
        try:
            # 尝试获取CSS选择器
            css_path = await element_handle.evaluate(f'element => {{ {js_functions} return getCssPath(element); }}')
            if css_path and css_path != 'body':
                return css_path
        except:
            pass
        
        return None


async def test_cover_preview_checker(page: Page) -> Dict[str, Any]:
    """
    测试封面预览检查器
    
    Args:
        page: Playwright页面对象
    
    Returns:
        Dict[str, Any]: 测试结果
    """
    checker = CoverPreviewChecker(page)
    
    tencent_logger.info("=" * 50)
    tencent_logger.info("开始测试封面预览检查器")
    tencent_logger.info("=" * 50)
    
    # 显示平台信息
    platform_info = checker.get_platform_info()
    tencent_logger.info(f"当前平台: {platform_info['platform_name']}")
    
    # 获取完整状态
    status = await checker.get_cover_preview_status()
    tencent_logger.info(f"封面预览状态: {status['message']}")
    
    # 等待准备就绪
    if not status['is_ready']:
        tencent_logger.info("等待封面预览准备就绪...")
        is_ready, message, element = await checker.wait_for_cover_preview_ready(timeout=30)
        
        if is_ready:
            tencent_logger.success(f"等待成功: {message}")
        else:
            tencent_logger.error(f"等待失败: {message}")
    
    # 尝试触发弹窗
    tencent_logger.info("尝试触发封面更换弹窗...")
    dialog_triggered = await checker.trigger_cover_change_dialog()
    
    if dialog_triggered:
        tencent_logger.success("✓ 封面更换弹窗触发成功")
    else:
        tencent_logger.error("✗ 封面更换弹窗触发失败")
    
    # 最终状态
    final_status = await checker.get_cover_preview_status()
    
    tencent_logger.info("=" * 50)
    tencent_logger.info("测试完成")
    tencent_logger.info("=" * 50)
    
    return {
        'platform_info': platform_info,
        'initial_status': status,
        'final_status': final_status,
        'dialog_triggered': dialog_triggered
    }


if __name__ == "__main__":
    # 测试用例
    async def test():
        print("腾讯视频号封面预览检查器测试")
        print("注意：此测试需要在腾讯视频号上传页面运行")
        
        # 这里只是一个演示，实际使用时需要传入真实的page对象
        print("测试完成 - 请在实际使用时传入Playwright页面对象")
    
    asyncio.run(test())