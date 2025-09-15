#!/usr/bin/env python3
"""
统计管理器 - 处理多平台统计数据获取
Statistics Manager - Handles multi-platform statistics acquisition
"""

import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from conf import BASE_DIR


class StatisticsManager:
    """统计管理器类"""

    # 平台统计获取函数映射
    StatsMapping = {
        'kuaishou': 'statistics.kuaishou_stat.get_kuaishou_statistics',
        'tencent': 'statistics.tencent_stat.get_tencent_statistics',
        'xiaohongshu': 'statistics.xiaohongshu_stat.get_xiaohongshu_statistics'
    }

    # 平台Cookie文件路径映射
    CookiePathMapping = {
        'kuaishou': 'cookies/ks_uploader/account.json',
        'tencent': 'cookies/tencent_uploader/account.json',
        'xiaohongshu': 'cookies/xiaohongshu_uploader/account.json'
    }

    # 平台显示名称
    PlatformNames = {
        'kuaishou': '快手',
        'tencent': '腾讯视频号',
        'xiaohongshu': '小红书',
    }

    # 平台描述和注意事项
    PlatformNotes = {
        'kuaishou': '支持粉丝数、关注数、获赞数统计',
        'tencent': '支持粉丝数、关注数、获赞数、视频数统计',
        'xiaohongshu': '支持粉丝数、关注数、获赞数、笔记数统计'
    }

    @classmethod
    def get_all_platforms(cls) -> Dict[str, str]:
        """获取所有支持统计的平台"""
        return cls.PlatformNames.copy()

    @classmethod
    def get_platform_notes(cls) -> Dict[str, str]:
        """获取平台注意事项"""
        return cls.PlatformNotes.copy()

    @classmethod
    def get_cookie_path(cls, platform: str) -> Path:
        """获取平台Cookie文件路径"""
        if platform in cls.CookiePathMapping:
            return BASE_DIR / cls.CookiePathMapping[platform]
        return BASE_DIR / f"cookies/{platform}_uploader/account.json"

    @classmethod
    def cookie_exists(cls, platform: str) -> bool:
        """检查Cookie文件是否存在"""
        cookie_path = cls.get_cookie_path(platform)
        return cookie_path.exists()

    @classmethod
    def get_platform_status(cls, platform: str) -> str:
        """获取平台统计状态"""
        if platform not in cls.StatsMapping:
            return "❌ 不支持"

        if not cls.cookie_exists(platform):
            return "❌ 缺少Cookie"

        return "✅ 可获取"

    @classmethod
    async def get_platform_statistics(cls, platform: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取指定平台的统计数据
        
        Args:
            platform: 平台名称
            debug: 是否启用调试模式
        
        Returns:
            统计数据字典，失败返回None
        """
        if platform not in cls.StatsMapping:
            print(f"❌ 平台 {platform} 不支持统计功能")
            return None

        if not cls.cookie_exists(platform):
            print(f"❌ {cls.PlatformNames.get(platform, platform)} Cookie文件不存在")
            print(f"   请先运行: python multi_get_cookies.py")
            return None

        try:
            # 动态导入统计函数
            module_path, function_name = cls.StatsMapping[platform].rsplit('.', 1)

            # 确保项目根目录在Python路径中
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # 使用映射表中的路径直接导入模块
            try:
                module = importlib.import_module(module_path)
                get_stats_func = getattr(module, function_name)
            except ImportError:
                # 如果失败，尝试使用备用路径
                if platform in ['kuaishou', 'ks']:
                    module = importlib.import_module('statistics.kuaishou_stat')
                elif platform in ['xiaohongshu', 'xhs']:
                    module = importlib.import_module('statistics.xiaohongshu_stat')
                elif platform in ['tencent']:
                    module = importlib.import_module('statistics.tencent_stat')
                else:
                    raise ImportError(f"无法导入 {platform} 的统计模块")
                
                get_stats_func = getattr(module, function_name)

            cookie_path = cls.get_cookie_path(platform)

            print(f"🔄 正在获取 {cls.PlatformNames.get(platform, platform)} 统计数据...")
            if debug:
                print("🔍 调试模式已启用，浏览器将保持打开状态")

            # 调用统计函数
            data = await get_stats_func(str(cookie_path), debug=debug)

            if data:
                print(f"✅ {cls.PlatformNames.get(platform, platform)} 统计数据获取成功")
                return data
            else:
                print(f"❌ {cls.PlatformNames.get(platform, platform)} 统计数据获取失败")
                return None

        except ImportError as e:
            print(f"❌ 无法导入 {platform} 的统计模块: {e}")
            return None
        except AttributeError as e:
            print(f"❌ {platform} 的统计函数不存在: {e}")
            return None
        except Exception as e:
            print(f"❌ 获取 {platform} 统计数据时出错: {e}")
            if debug:
                print("🔍 调试模式已启用，浏览器可能保持打开状态以便调试")
                print("请检查浏览器中的错误状态，然后按回车键继续...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("⚠️  用户中断调试")
            return None

    @classmethod
    async def get_multiple_statistics(cls, platforms: List[str], debug: bool = False) -> Dict[
        str, Optional[Dict[str, Any]]]:
        """
        批量获取多个平台的统计数据
        
        Args:
            platforms: 平台列表
            debug: 是否启用调试模式
        
        Returns:
            各平台统计数据字典
        """
        results = {}

        print("🚀 开始批量获取统计数据...")
        print(f"📱 目标平台: {', '.join([cls.PlatformNames.get(p, p) for p in platforms])}")
        if debug:
            print("🔍 调试模式已启用，每个平台都会保持浏览器打开")

        for i, platform in enumerate(platforms, 1):
            print(f"\n{'=' * 60}")
            print(f"📊 进度: {i}/{len(platforms)} - {cls.PlatformNames.get(platform, platform)}")
            print(f"{'=' * 60}")

            data = await cls.get_platform_statistics(platform, debug)
            results[platform] = data

        return results

    @classmethod
    def print_statistics_summary(cls, results: Dict[str, Optional[Dict[str, Any]]]):
        """打印统计数据获取结果汇总"""
        print(f"\n{'=' * 70}")
        print("📊 统计数据获取结果汇总")
        print(f"{'=' * 70}")

        success_count = sum(1 for data in results.values() if data is not None)
        total_count = len(results)

        for platform, data in results.items():
            if data is not None:
                status = "✅ 成功"
                followers = data.get('followers', 0)
                following = data.get('following', 0)
                likes = data.get('likes', 0)
                videos = data.get('videos_count', 0)

                info = f"粉丝: {followers:,} | 关注: {following:,} | 获赞: {likes:,}"
                if videos > 0:
                    info += f" | 视频: {videos:,}"
            else:
                status = "❌ 失败"
                info = "无数据"

            platform_name = cls.PlatformNames.get(platform, platform)
            print(f"   {platform_name:10} ({platform:8}) - {status}")
            print(f"   {'':21} {info}")

        print(f"\n📈 总计: {success_count}/{total_count} 成功")

        if success_count == total_count:
            print("🎉 所有平台统计数据获取完成！")
        elif success_count == 0:
            print("💥 所有平台统计数据获取失败！")
        else:
            print("⚠️  部分平台统计数据获取失败，请检查Cookie和网络连接")

    @classmethod
    def generate_statistics_report(cls, results: Dict[str, Optional[Dict[str, Any]]], output_dir: str = "reports"):
        """生成统计报告"""
        from datetime import datetime

        output_path = Path(output_dir) / "multi_platform_stats"
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成JSON报告
        json_file = output_path / f"multi_platform_stats_{timestamp}.json"
        import json

        report_data = {
            'timestamp': datetime.now().isoformat(),
            'platforms': list(results.keys()),
            'results': results,
            'summary': {
                'total_platforms': len(results),
                'successful_platforms': sum(1 for data in results.values() if data is not None),
                'failed_platforms': sum(1 for data in results.values() if data is None)
            }
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"📄 统计报告已生成: {json_file}")

        # 生成Markdown报告
        md_file = output_path / f"multi_platform_stats_{timestamp}.md"

        md_content = f"""# 多平台统计数据报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 统计概览

- 总平台数: {len(results)}
- 成功获取: {sum(1 for data in results.values() if data is not None)}
- 获取失败: {sum(1 for data in results.values() if data is None)}

## 📱 各平台数据

"""

        for platform, data in results.items():
            platform_name = cls.PlatformNames.get(platform, platform)
            md_content += f"### {platform_name} ({platform})\n\n"

            if data is not None:
                md_content += f"- 粉丝数: {data.get('followers', 0):,}\n"
                md_content += f"- 关注数: {data.get('following', 0):,}\n"
                md_content += f"- 获赞数: {data.get('likes', 0):,}\n"
                if data.get('videos_count', 0) > 0:
                    md_content += f"- 视频数: {data.get('videos_count', 0):,}\n"
                md_content += f"- 获取时间: {data.get('timestamp', '未知')}\n"
            else:
                md_content += "- ❌ 数据获取失败\n"

            md_content += "\n"

        md_content += f"""
---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*由 multi_platform_get_stats.py 自动生成*
"""

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"📄 Markdown报告已生成: {md_file}")

        return [str(json_file), str(md_file)]
