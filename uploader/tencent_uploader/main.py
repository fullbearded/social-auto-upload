# -*- coding: utf-8 -*-
from datetime import datetime

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import tencent_logger


def format_str_for_short_title(origin_title: str) -> str:
    # 定义允许的特殊字符
    allowed_special_chars = "《》“”:+?%°"

    # 移除不允许的特殊字符
    filtered_chars = [char if char.isalnum() or char in allowed_special_chars else ' ' if char == ',' else '' for
                      char in origin_title]
    formatted_string = ''.join(filtered_chars)

    # 调整字符串长度
    if len(formatted_string) > 16:
        # 截断字符串
        formatted_string = formatted_string[:16]
    elif len(formatted_string) < 6:
        # 使用空格来填充字符串
        formatted_string += ' ' * (6 - len(formatted_string))

    return formatted_string


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[+] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[+] cookie 有效")
            return True


async def get_tencent_cookie(account_file):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


async def weixin_setup(account_file, handle=False):
    account_file = get_absolute_path(account_file, "tencent_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        tencent_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await get_tencent_cookie(account_file)
    return True


class TencentVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, category=None,
                 thumbnail_path=None):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.category = category
        self.thumbnail_path = thumbnail_path
        self.local_executable_path = LOCAL_CHROME_PATH

    async def set_schedule_time_tencent(self, page, publish_date):
        try:
            tencent_logger.info(f"设置定时发布时间: {publish_date}")

            # 点击定时选项
            timing_label = page.locator("label").filter(has_text="定时").nth(1)
            if await timing_label.count() > 0:
                await timing_label.click()
                tencent_logger.info("点击了定时选项")
                await page.wait_for_timeout(1000)

            # 点击日期时间输入框
            datetime_input = page.locator('input[placeholder="请选择发表时间"]')
            if await datetime_input.count() > 0:
                await datetime_input.click()
                tencent_logger.info("点击了日期时间输入框")
                await page.wait_for_timeout(1500)

            # 获取当前显示的年月
            year_label = await page.locator('span.weui-desktop-picker__panel__label').first.inner_text()
            month_label = await page.locator('span.weui-desktop-picker__panel__label').nth(1).inner_text()

            target_year = f"{publish_date.year}年"
            target_month = f"{publish_date.month:02d}月"

            tencent_logger.info(f"当前显示: {year_label} {month_label}, 目标: {target_year} {target_month}")

            # 如果年份不匹配，需要切换年份（这里简化处理，假设在同一年的范围内）
            if year_label != target_year:
                tencent_logger.warning("年份不匹配，可能需要手动调整")

            # 切换到目标月份
            if month_label != target_month:
                # 简单的月份切换逻辑：如果当前月份小于目标月份，点击右箭头，否则点击左箭头
                current_month_num = int(month_label.replace("月", ""))
                target_month_num = publish_date.month

                if current_month_num < target_month_num:
                    # 需要点击右箭头增加月份
                    right_arrow = page.locator('button.weui-desktop-btn__icon__right')
                    for _ in range(target_month_num - current_month_num):
                        await right_arrow.click()
                        await page.wait_for_timeout(500)
                else:
                    # 需要点击左箭头减少月份
                    left_arrow = page.locator('button.weui-desktop-btn__icon__left')
                    for _ in range(current_month_num - target_month_num):
                        await left_arrow.click()
                        await page.wait_for_timeout(500)

                await page.wait_for_timeout(1000)

            # 选择目标日期
            target_day = str(publish_date.day)
            day_elements = page.locator('table.weui-desktop-picker__table a')

            if await day_elements.count() > 0:
                day_found = False
                for i in range(await day_elements.count()):
                    element = day_elements.nth(i)
                    class_name = await element.get_attribute('class') or ''

                    # 跳过禁用的日期
                    if 'weui-desktop-picker__disabled' in class_name:
                        continue

                    day_text = await element.inner_text()
                    if day_text.strip() == target_day:
                        await element.click()
                        tencent_logger.info(f"选择了日期: {target_day}")
                        day_found = True
                        break

                if not day_found:
                    tencent_logger.warning(f"未找到可用日期: {target_day}")
            else:
                tencent_logger.warning("未找到日期选择元素")

            await page.wait_for_timeout(1000)

            # 设置时间
            time_input = page.locator('input[placeholder="请选择时间"]')
            if await time_input.count() > 0:
                await time_input.click()
                tencent_logger.info("点击了时间输入框")
                await page.wait_for_timeout(1000)

                # 选择小时
                hour_options = page.locator('.weui-desktop-picker__time__hour li')
                if await hour_options.count() > 0:
                    target_hour = f"{publish_date.hour:02d}"
                    hour_found = False
                    for i in range(await hour_options.count()):
                        hour_text = await hour_options.nth(i).inner_text()
                        if hour_text == target_hour:
                            await hour_options.nth(i).click()
                            tencent_logger.info(f"选择了小时: {target_hour}")
                            hour_found = True
                            break

                    if not hour_found:
                        tencent_logger.warning(f"未找到小时选项: {target_hour}")

                await page.wait_for_timeout(500)

                # 选择分钟
                minute_options = page.locator('.weui-desktop-picker__time__minute li')
                if await minute_options.count() > 0:
                    target_minute = f"{publish_date.minute:02d}"
                    minute_found = False
                    for i in range(await minute_options.count()):
                        minute_text = await minute_options.nth(i).inner_text()
                        if minute_text == target_minute:
                            await minute_options.nth(i).click()
                            tencent_logger.info(f"选择了分钟: {target_minute}")
                            minute_found = True
                            break

                    if not minute_found:
                        tencent_logger.warning(f"未找到分钟选项: {target_minute}")

            # 点击其他区域确认时间选择
            await page.locator("div.input-editor").click()
            tencent_logger.success("定时发布时间设置完成")

        except Exception as e:
            tencent_logger.error(f"设置定时发布时间时出错: {e}")
            # 出错时不影响视频上传，继续执行

    async def _wait_for_page_ready(self, page):
        """等待页面完全加载完成"""
        try:
            tencent_logger.info("等待页面完全加载...")

            # 等待主要元素加载完成
            await page.wait_for_selector('div.input-editor', timeout=30000)
            tencent_logger.info("✓ 编辑器区域已加载")

            # 等待文件上传区域
            await page.wait_for_selector('input[type="file"]', timeout=10000)
            tencent_logger.info("✓ 文件上传区域已加载")

            # 等待位置选择区域加载
            try:
                await page.wait_for_selector('.position-display-wrap, .location-filter-wrap', timeout=10000)
                tencent_logger.info("✓ 位置选择区域已加载")
            except:
                tencent_logger.info("⚠ 位置选择区域加载超时，继续执行")

            # 等待网络请求完成
            await page.wait_for_load_state('networkidle', timeout=15000)
            tencent_logger.info("✓ 网络请求已完成")

            # 额外等待一段时间确保页面稳定
            await page.wait_for_timeout(2000)
            tencent_logger.info("✓ 页面完全加载完成")

        except Exception as e:
            tencent_logger.warning(f"页面加载检测超时或出错: {e}")
            tencent_logger.info("继续执行上传流程...")

    async def _wait_for_thumbnail_area_ready(self, page):
        """等待缩略图区域准备就绪"""
        try:
            tencent_logger.info("等待缩略图区域加载...")

            # 等待包含"封面预览"的区域出现
            cover_preview_area = page.locator("div.label:has-text('封面预览')")
            await cover_preview_area.wait_for(timeout=20000)
            tencent_logger.info("✓ 封面预览区域已加载")

            # 在封面预览区域中等待编辑按钮出现
            edit_button = page.locator("div.label:has-text('封面预览') >> xpath=.. >> div.edit-btn, div.label:has-text('封面预览') >> xpath=.. >> div.edit-btn-zIndex")
            await edit_button.wait_for(timeout=10000)
            tencent_logger.info("✓ 缩略图编辑按钮已加载")

            # 额外等待确保页面稳定
            await page.wait_for_timeout(1000)
            tencent_logger.info("✓ 缩略图区域准备完成")

        except Exception as e:
            tencent_logger.warning(f"缩略图区域检测超时或出错: {e}")
            tencent_logger.info("继续尝试设置缩略图...")

    async def handle_upload_error(self, page):
        tencent_logger.info("视频出错了，重新上传中")
        await page.locator('div.media-status-content div.tag-inner:has-text("删除")').click()
        await page.get_by_role('button', name="删除", exact=True).click()
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium (这里使用系统内浏览器，用chromium 会造成h264错误
        browser = await playwright.chromium.launch(headless=False, executable_path=self.local_executable_path)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        tencent_logger.info(f'[+]正在上传-------{self.title}.mp4')

        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        await page.wait_for_url("https://channels.weixin.qq.com/platform/post/create")

        # 等待页面完全加载
        await self._wait_for_page_ready(page)
        # await page.wait_for_selector('input[type="file"]', timeout=10000)
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(self.file_path)
        # 填充标题和话题
        await self.add_title_tags(page)
        tencent_logger.info("1. 填充标题和话题")
        # 添加商品
        # await self.add_product(page)
        # 设置缩略图（如果有）
        await asyncio.sleep(3)
        if self.thumbnail_path:
            await self.set_thumbnail(page)
        tencent_logger.info("2. 设置缩略图")
        await asyncio.sleep(3)
        await self.set_location(page, None)
        tencent_logger.info("3. 设置位置")

        # 合集功能
        await self.add_collection(page)
        tencent_logger.info("4. 添加合集")
        # 原创选择
        await self.add_original(page)
        tencent_logger.info("5. 选择原创")
        # 检测上传状态
        await self.detect_upload_status(page)

        # 设置时间
        if self.publish_date != 0:
            await self.set_schedule_time_tencent(page, self.publish_date)
        tencent_logger.info("6. 设置发布时间")
        # 添加短标题
        await self.add_short_title(page)
        tencent_logger.info("7. 添加短标题")

        # DEBUG
        await asyncio.sleep(3)  # 这里延迟是为了方便眼睛直观的观看

        await self.click_publish(page)

        await context.storage_state(path=f"{self.account_file}")  # 保存cookie
        tencent_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def set_location(self, page, location: str = "成都市"):
        try:
            # 如果location为None或空字符串，选择"不显示位置"
            if location is None or location.strip() == "":
                tencent_logger.info("位置为空，选择不显示位置")

                # 尝试点击位置选择器以展开选项，优先点击位置显示区域
                location_display = page.locator('.position-display-wrap')
                if await location_display.count() > 0:
                    await location_display.click()
                    tencent_logger.info("点击了位置显示区域")
                    await page.wait_for_timeout(1000)
                else:
                    # 如果没有位置显示区域，尝试点击位置过滤区域
                    location_filter = page.locator('.location-filter-wrap')
                    if await location_filter.count() > 0:
                        await location_filter.click()
                        tencent_logger.info("点击了位置过滤区域")
                        await page.wait_for_timeout(1000)

                # 查找"不显示位置"选项
                no_location_option = page.locator('.option-item .location-item .name:has-text("不显示位置")')
                if await no_location_option.count() > 0:
                    await no_location_option.click()
                    tencent_logger.success("成功选择不显示位置")
                else:
                    # 如果没有找到"不显示位置"，尝试点击第一个选项
                    first_option = page.locator('.option-item').first
                    if await first_option.count() > 0:
                        await first_option.click()
                        option_text = await first_option.locator('.name').inner_text()
                        tencent_logger.info(f"选择第一个位置选项: {option_text}")
                return

            # location不为None时，正常设置位置

            # 先尝试点击位置输入区域
            location_input = page.locator(
                'input[placeholder="搜索附近位置"], .weui-desktop-form__input[placeholder*="位置"]')
            if await location_input.count() > 0:
                await location_input.click()
                tencent_logger.info("点击了位置输入框")
            else:
                # 如果没有找到输入框，尝试点击位置选择器
                location_display = page.locator('.position-display-wrap')
                if await location_display.count() > 0:
                    await location_display.click()
                    tencent_logger.info("点击了位置显示区域")
                else:
                    location_filter = page.locator('.location-filter-wrap')
                    if await location_filter.count() > 0:
                        await location_filter.click()
                        tencent_logger.info("点击了位置过滤区域")
                    else:
                        # 尝试点击"添加位置"或类似按钮
                        add_location_btn = page.locator('button:has-text("添加位置"), .location-btn')
                        if await add_location_btn.count() > 0:
                            await add_location_btn.click()
                            tencent_logger.info("点击了添加位置按钮")

            await page.wait_for_timeout(1000)

            # 清空现有内容并输入新位置
            search_input = page.locator('input[placeholder="搜索附近位置"], .weui-desktop-form__input')
            if await search_input.count() > 0:
                await search_input.fill(location)
                tencent_logger.info(f"输入位置: {location}")

                # 等待搜索结果
                await page.wait_for_timeout(2000)

                # 查找包含目标位置的选项
                location_options = page.locator('.option-item .location-item .name')
                if await location_options.count() > 0:
                    # 遍历选项找到匹配的位置
                    options_count = await location_options.count()
                    found = False
                    for i in range(options_count):
                        option_text = await location_options.nth(i).inner_text()
                        if location in option_text:
                            await location_options.nth(i).click()
                            tencent_logger.success(f"成功选择位置: {option_text}")
                            found = True
                            break

                    # 如果没有找到完全匹配的，选择第一个有效选项
                    if not found:
                        await location_options.first.click()
                        selected_text = await location_options.first.inner_text()
                        tencent_logger.info(f"选择第一个位置选项: {selected_text}")
                else:
                    # 如果没有选项列表，直接按回车
                    await page.keyboard.press("Enter")
                    tencent_logger.info("按下回车确认位置")
            else:
                tencent_logger.warning("未找到位置输入框")

        except Exception as e:
            tencent_logger.error(f"设置位置时出错: {e}")
            # 出错时不影响视频上传，继续执行

    async def add_short_title(self, page):
        short_title_element = page.get_by_text("短标题", exact=True).locator("..").locator(
            "xpath=following-sibling::div").locator(
            'span input[type="text"]')
        if await short_title_element.count():
            short_title = format_str_for_short_title(self.title)
            await short_title_element.fill(short_title)

    async def click_publish(self, page):
        while True:
            try:
                publish_buttion = page.locator('div.form-btns button:has-text("发表")')
                if await publish_buttion.count():
                    await publish_buttion.click()
                await page.wait_for_url("https://channels.weixin.qq.com/platform/post/list", timeout=5000)
                tencent_logger.success("  [-]视频发布成功")
                break
            except Exception as e:
                current_url = page.url
                if "https://channels.weixin.qq.com/platform/post/list" in current_url:
                    tencent_logger.success("  [-]视频发布成功")
                    break
                else:
                    tencent_logger.exception(f"  [-] Exception: {e}")
                    tencent_logger.info("  [-] 视频正在发布中...")
                    await asyncio.sleep(0.5)

    async def detect_upload_status(self, page):
        while True:
            # 匹配删除按钮，代表视频上传完毕，如果不存在，代表视频正在上传，则等待
            try:
                # 匹配删除按钮，代表视频上传完毕
                if "weui-desktop-btn_disabled" not in await page.get_by_role("button", name="发表").get_attribute(
                        'class'):
                    tencent_logger.info("  [-]视频上传完毕")
                    break
                else:
                    tencent_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)
                    # 出错了视频出错
                    if await page.locator('div.status-msg.error').count() and await page.locator(
                            'div.media-status-content div.tag-inner:has-text("删除")').count():
                        tencent_logger.error("  [-] 发现上传出错了...准备重试")
                        await self.handle_upload_error(page)
            except:
                tencent_logger.info("  [-] 正在上传视频中...")
                await asyncio.sleep(2)

    async def add_title_tags(self, page):
        await page.locator("div.input-editor").click()
        await page.keyboard.type(self.title)
        await page.keyboard.press("Enter")
        for index, tag in enumerate(self.tags, start=1):
            await page.keyboard.type("#" + tag)
            await page.keyboard.press("Space")
        tencent_logger.info(f"成功添加hashtag: {len(self.tags)}")

    async def set_thumbnail(self, page):
        """设置视频缩略图"""
        try:
            tencent_logger.info(f"设置缩略图: {self.thumbnail_path}")
            # 等待视频上传完成和页面稳定
            await asyncio.sleep(3)
            await self._wait_for_thumbnail_area_ready(page)

            await asyncio.sleep(10)
            # 尝试方法1：通过编辑封面按钮设置
            await self._set_thumbnail_via_edit_button(page)
            
        except Exception as e:
            tencent_logger.error(f"设置缩略图时出错: {e}")
            # 缩略图设置失败不影响视频上传，继续执行

    async def _set_thumbnail_via_edit_button(self, page):
        """通过编辑封面按钮设置缩略图"""
        try:
            # 点击封面预览区域中的编辑按钮
            edit_button = page.locator("div.cover-preview-wrap div:has-text('编辑')")
            
            if await edit_button.count() > 0:
                await edit_button.first.click()
                tencent_logger.info("点击了封面预览区域的编辑按钮")
                await asyncio.sleep(2)
                
                # 等待弹窗出现
                await page.wait_for_selector("div.cover-set-wrap", timeout=10000)
                tencent_logger.info("✓ 缩略图设置弹窗已出现")
                
                # 查找图片类型的文件上传输入框
                image_file_input = page.locator("input[type='file'][accept*='image']")
                tencent_logger.info("DEBUG 查找图片上传输入框")
                if await image_file_input.count() > 0:
                    tencent_logger.info("DEBUG 找到图片上传输入框")
                    await image_file_input.set_input_files(self.thumbnail_path)
                    tencent_logger.info("缩略图文件已选择")
                    await asyncio.sleep(3)
                    
                    # 确认缩略图设置
                    await self._confirm_thumbnail_setting(page)
                else:
                    tencent_logger.info("DEBUG 未找到图片上传输入框，尝试其他方式")
                    # 如果没有找到专门的图片上传框，尝试使用可见的文件输入框
                    await self._set_thumbnail_via_visible_inputs(page)
            else:
                tencent_logger.warning("未找到封面预览区域的编辑按钮，尝试其他方式")
                # 尝试其他方法
                await self._set_thumbnail_via_cover_area(page)
                
        except Exception as e:
            tencent_logger.error(f"通过编辑按钮设置缩略图失败: {e}")
            # 尝试缩略图区域方式作为备选
            await self._set_thumbnail_via_cover_area(page)

    async def _set_thumbnail_via_visible_inputs(self, page):
        """通过可见的文件输入框设置缩略图"""
        try:
            visible_file_inputs = page.locator("input[type='file']:visible")
            if await visible_file_inputs.count() > 0:
                # 优先选择第二个可见的文件输入框（通常是图片上传）
                if await visible_file_inputs.count() > 1:
                    await visible_file_inputs.nth(1).set_input_files(self.thumbnail_path)
                else:
                    await visible_file_inputs.first.set_input_files(self.thumbnail_path)
                tencent_logger.info("通过可见输入框设置缩略图文件")
                await asyncio.sleep(2)
                
                # 确认缩略图设置
                await self._confirm_thumbnail_setting(page)
            else:
                tencent_logger.warning("未找到可见的文件输入框")
        except Exception as e:
            tencent_logger.error(f"通过可见输入框设置缩略图失败: {e}")

    async def _set_thumbnail_direct_upload(self, page):
        """直接上传缩略图文件"""
        try:
            # 方法1：查找图片类型的文件上传输入框
            image_file_input = page.locator("input[type='file'][accept*='image']")
            if await image_file_input.count() > 0:
                await image_file_input.set_input_files(self.thumbnail_path)
                tencent_logger.info("直接设置缩略图文件")
                await asyncio.sleep(3)
            else:
                # 方法2：如果没有找到专门的图片上传框，查找所有文件输入框
                await self._set_thumbnail_via_all_inputs(page)
        except Exception as e:
            tencent_logger.error(f"直接上传缩略图失败: {e}")

    async def _set_thumbnail_via_cover_area(self, page):
        """通过缩略图区域直接点击设置"""
        try:
            # 根据提供的HTML结构，查找缩略图区域
            cover_area = page.locator("div.vertical-cover-wrap, div.img-popover-wrap, div.vertical-img-wrap")
            
            if await cover_area.count() > 0:
                await cover_area.first.click()
                tencent_logger.info("点击了缩略图区域")
                await asyncio.sleep(2)
                
                # 查找图片类型的文件上传输入框
                image_file_input = page.locator("input[type='file'][accept*='image']")
                if await image_file_input.count() > 0:
                    await image_file_input.set_input_files(self.thumbnail_path)
                    tencent_logger.info("缩略图文件已选择")
                    await asyncio.sleep(3)
                    
                    # 确认缩略图设置
                    await self._confirm_thumbnail_setting(page)
                else:
                    tencent_logger.warning("未找到图片上传输入框")
            else:
                tencent_logger.warning("未找到缩略图区域")
                
        except Exception as e:
            tencent_logger.error(f"通过缩略图区域设置失败: {e}")
            # 最后尝试直接上传方式
            await self._set_thumbnail_direct_upload(page)

    async def _set_thumbnail_via_all_inputs(self, page):
        """通过所有文件输入框设置缩略图"""
        try:
            all_file_inputs = page.locator("input[type='file']")
            if await all_file_inputs.count() > 0:
                # 优先选择accept属性包含image的输入框
                found = False
                for i in range(await all_file_inputs.count()):
                    input_element = all_file_inputs.nth(i)
                    accept_attr = await input_element.get_attribute('accept') or ''
                    if 'image' in accept_attr:
                        await input_element.set_input_files(self.thumbnail_path)
                        tencent_logger.info("通过image属性输入框设置缩略图文件")
                        await asyncio.sleep(2)
                        found = True
                        break

                # 如果没有找到，选择第二个文件输入框（通常是图片上传）
                if not found and await all_file_inputs.count() > 1:
                    await all_file_inputs.nth(1).set_input_files(self.thumbnail_path)
                    tencent_logger.info("通过第二个输入框设置缩略图文件")
                    await asyncio.sleep(2)
                elif not found:
                    tencent_logger.warning("未找到合适的文件输入框")
            else:
                tencent_logger.warning("未找到任何文件输入框")
        except Exception as e:
            tencent_logger.error(f"通过所有输入框设置缩略图失败: {e}")

    async def _confirm_thumbnail_setting(self, page):
        """确认缩略图设置"""
        try:
            # 等待一段时间确保缩略图上传完成
            await asyncio.sleep(2)
            
            # 根据提供的HTML结构，精确定位确认按钮
            confirm_button = page.locator("div.weui-desktop-dialog__ft div.cover-set-footer .weui-desktop-btn_wrp:last-child button.weui-desktop-btn_primary")
            
            if await confirm_button.count() > 0:
                await confirm_button.click()
                tencent_logger.success("缩略图设置成功")
                await asyncio.sleep(1)
            else:
                # 备用方案：尝试其他可能的确认按钮选择器
                fallback_confirm_button = page.locator("button:has-text('确认'), button:has-text('确定'), button:has-text('完成')")
                if await fallback_confirm_button.count() > 0:
                    await fallback_confirm_button.first.click()
                    tencent_logger.success("缩略图设置成功（备用方案）")
                    await asyncio.sleep(1)
                else:
                    tencent_logger.info("未找到确认按钮，可能已自动确认")
                
        except Exception as e:
            tencent_logger.error(f"确认缩略图设置时出错: {e}")
            tencent_logger.info("可能已自动确认")

    async def add_collection(self, page):
        collection_elements = page.get_by_text("添加到合集").locator("xpath=following-sibling::div").locator(
            '.option-list-wrap > div')
        if await collection_elements.count() > 1:
            await page.get_by_text("添加到合集").locator("xpath=following-sibling::div").click()
            await collection_elements.first.click()

    async def add_original(self, page):
        if await page.get_by_label("视频为原创").count():
            await page.get_by_label("视频为原创").check()
        # 检查 "我已阅读并同意 《视频号原创声明使用条款》" 元素是否存在
        label_locator = await page.locator('label:has-text("我已阅读并同意 《视频号原创声明使用条款》")').is_visible()
        if label_locator:
            await page.get_by_label("我已阅读并同意 《视频号原创声明使用条款》").check()
            await page.get_by_role("button", name="声明原创").click()
        # 2023年11月20日 wechat更新: 可能新账号或者改版账号，出现新的选择页面
        if await page.locator('div.label span:has-text("声明原创")').count() and self.category:
            # 因处罚无法勾选原创，故先判断是否可用
            if not await page.locator('div.declare-original-checkbox input.ant-checkbox-input').is_disabled():
                await page.locator('div.declare-original-checkbox input.ant-checkbox-input').click()
                if not await page.locator(
                        'div.declare-original-dialog label.ant-checkbox-wrapper.ant-checkbox-wrapper-checked:visible').count():
                    await page.locator('div.declare-original-dialog input.ant-checkbox-input:visible').click()
            if await page.locator('div.original-type-form > div.form-label:has-text("原创类型"):visible').count():
                await page.locator('div.form-content:visible').click()  # 下拉菜单
                await page.locator(
                    f'div.form-content:visible ul.weui-desktop-dropdown__list li.weui-desktop-dropdown__list-ele:has-text("{self.category}")').first.click()
                await page.wait_for_timeout(1000)
            if await page.locator('button:has-text("声明原创"):visible').count():
                await page.locator('button:has-text("声明原创"):visible').click()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
