#!/usr/bin/env python3
"""
界面管理器 - 处理用户交互和界面输出
UI Manager - Handles user interaction and interface output
"""

import sys
from typing import List, Dict, Optional
from utils.scheduler.platform_manager import PlatformManager
from datetime import datetime


class UIManager:
    """界面管理器类"""
    
    @staticmethod
    def print_scheduler_header():
        """打印调度器标题"""
        print("=" * 60)
        print("多平台智能视频调度发布器")
        print("支持平台: 抖音/哔哩哔哩/小红书/快手/百家号/腾讯/快手")
        print("=" * 60)
    
    @staticmethod
    def select_platforms() -> List[str]:
        """选择要发布的平台"""
        available_platforms = PlatformManager.get_all_platforms()
        platform_list = list(available_platforms.items())
        platform_notes = PlatformManager.get_platform_notes()
        
        print("\n📱 请选择要发布的平台（输入平台编号，多个平台用逗号分隔）:")
        
        for i, (key, name) in enumerate(platform_list, 1):
            note = platform_notes.get(key, '')
            note_str = f" - {note}" if note else ""
            print(f"  {i}. {name} ({key}){note_str}")
        
        print("\n💡 示例输入: 1,2,3  (表示选择抖音、哔哩哔哩、小红书)")
        print("   直接按回车使用默认配置: 腾讯视频号")
        
        try:
            user_input = input("\n请选择平台: ").strip()
            
            if not user_input:  # 默认配置
                return ['tencent']
            
            selected_indices = []
            for part in user_input.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(platform_list):
                        selected_indices.append(idx - 1)
            
            if selected_indices:
                selected_platforms = [platform_list[i][0] for i in selected_indices]
                display_names = PlatformManager.get_display_names(selected_platforms)
                platform_str = ', '.join([f"{p}({display_names[p]})" for p in selected_platforms])
                print(f"✅ 已选择平台: {platform_str}")
                return selected_platforms
            else:
                print("⚠️  输入无效，使用默认配置")
                return ['tencent']
                
        except (KeyboardInterrupt, EOFError):
            print("\n❌ 用户取消选择")
            return ['tencent']
        except Exception as e:
            print(f"❌ 选择平台时出错: {e}")
            return ['tencent']
    
    @staticmethod
    def get_tencent_account_type() -> str:
        """获取腾讯账号类型"""
        print("\n🛡️  腾讯风控保护系统")
        account_types = {
            "new": "新账号 (≤2周，≤10次上传)",
            "standard": "标准账号 (≤2个月，≤100次上传)",
            "mature": "成熟账号 (>2个月，>100次上传)"
        }
        
        print("请选择腾讯账号类型:")
        for key, desc in account_types.items():
            print(f"  {key}: {desc}")
        
        try:
            choice = input("腾讯账号类型 (默认为standard): ").strip().lower()
            if choice in ["new", "standard", "mature"]:
                return choice
        except:
            pass
        
        return "standard"
    
    @staticmethod
    def print_config_preview(platforms: List[str], daily_publish_times: List[int], 
                           group_size: int, available_platforms: Dict[str, str]):
        """打印配置预览"""
        display_names = PlatformManager.get_display_names(platforms)
        
        print(f"\n📅 发布时间: {[f'{t}:00' for t in daily_publish_times]}")
        print(f"📊 每组视频: {group_size}个")
        print(f"🚀 发布平台: {', '.join([f'{p}({display_names[p]})' for p in platforms])}")
    
    @staticmethod
    def print_video_count(total_videos: int):
        """打印视频数量"""
        print(f"📹 发现视频: {total_videos}个")
    
    @staticmethod
    def print_shuffle_results(original_videos: List[str], shuffled_videos: List[str]):
        """打印打乱结果"""
        print(f"\n=== 🎲 视频随机打乱结果 ===")
        print(f"原始顺序: {original_videos}")
        print(f"打乱顺序: {shuffled_videos}")
    
    @staticmethod
    def print_remainder_warning(remainder_count: int):
        """打印余数处理警告"""
        if remainder_count > 0:
            print(f"\n⚠️  特殊处理:")
            print(f"   余数视频: {remainder_count}个")
            print(f"   处理方式: 放在最后一天的前几个时间点")
    
    @staticmethod
    def print_final_summary(schedule_info: Dict, total_videos: int, 
                          available_platforms: Dict[str, str]):
        """打印最终摘要"""
        print(f"\n📋 总结:")
        print(f"   总视频数: {total_videos}")
        print(f"   发布天数: {schedule_info['total_days']}")
        print(f"   完整组数: {len(schedule_info['groups'])}")
        print(f"   余数处理: {'是' if schedule_info['remainder_videos'] else '否'}")
    
    @staticmethod
    def get_user_confirmation(message: str = "🤔 确认执行发布计划？ (y/N): ") -> bool:
        """获取用户确认"""
        try:
            confirm = input(message)
            return confirm.lower() == 'y'
        except (KeyboardInterrupt, EOFError):
            return False
    
    @staticmethod
    def print_start_message():
        """打印开始发布消息"""
        print(f"\n🚀 === 开始智能发布 === 🚀")
    
    @staticmethod
    def print_platform_header(platform: str):
        """打印平台标题"""
        print(f"\n{'='*50}")
        print(f"📱 发布到 {platform.upper()} 平台")
        print(f"{'='*50}")
    
    @staticmethod
    def print_cookie_success(platform: str):
        """打印Cookie验证成功消息"""
        print(f"✅ {platform} Cookie验证成功")
    
    @staticmethod
    def print_cookie_failed(platform: str):
        """打印Cookie验证失败消息"""
        print(f"❌ {platform} Cookie设置失败，跳过该平台")
    
    @staticmethod
    def print_daily_header(day: int):
        """打印每日发布计划标题"""
        print(f"\n📅 第{day}天发布计划:")
    
    @staticmethod
    def print_upload_result(video_name: str, success: bool, current: int, total: int):
        """打印上传结果"""
        if success:
            print(f"✅ {current}/{total} 完成: {video_name}")
        else:
            print(f"❌ {current}/{total} 失败: {video_name}")
    
    @staticmethod
    def print_delay_message(delay_seconds: int, platform_name: str):
        """打印延迟消息"""
        if platform_name == 'kuaishou':
            print(f"⏳ 快手间隔: {delay_seconds}秒...")
    
    @staticmethod
    def print_platform_complete_stats(platform: str, total_videos: int, 
                                    success_count: int, fail_count: int,
                                    has_risk_control: bool = False, 
                                    account_type: str = None):
        """打印平台完成统计"""
        success_rate = (success_count / total_videos * 100) if total_videos > 0 else 0.0
        
        print(f"\n{'='*50}")
        print(f"📈 {platform.upper()} 平台发布完成统计:")
        print(f"   总视频数: {total_videos}")
        print(f"   成功: {success_count}")
        print(f"   失败: {fail_count}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if has_risk_control and account_type:
            print(f"   风控保护: 已启用({account_type}账号)")
    
    @staticmethod
    def print_final_completion_stats(total_videos: int, schedule_info: Dict,
                                   available_platforms: Dict[str, str]):
        """打印最终完成统计"""
        print(f"\n🎉 === 多平台智能发布完成 === 🎉")
        print(f"📊 最终统计报告:")
        print(f"   📹 总视频数: {total_videos}")
        print(f"   📅 发布天数: {schedule_info['total_days']}")
        print(f"   🎲 随机打乱: ✅")
        print(f"   📊 智能分组: ✅")
        print(f"   🎯 余数处理: ✅")
        print(f"   ⏰ 随机偏移: ✅")
        print(f"   🛡️ 风控保护: ✅")
        print(f"   🌐 支持平台: {len(available_platforms)}个")
        
        now = datetime.now()
        print(f"\n💡 文件名: upload_log_{now.strftime('%Y%m%d_%H%M%S')}.log")
        print(f"🚀 多平台智能视频调度发布器 - 任务完成！")
    
    @staticmethod
    def print_risk_control_info(risk_controller):
        """打印风控信息"""
        if not risk_controller:
            return
            
        stats = risk_controller.get_daily_stats(datetime.now().date())
        print(f"\n🛡️  腾讯风控最终分析:")
        print(f"   账号类型: {risk_controller.account_type}")
        print(f"   风控策略: ✅ 已启用")
        print(f"   风控事件: {stats['risk_incidents']} 次")
        print(f"   日志位置: logs/tencent_risk_*.log")