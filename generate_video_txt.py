#!/usr/bin/env python3
"""
视频文件名处理器
功能：遍历目录中的MP4文件，基于文件名规则生成.txt文件
支持自定义文案和标签功能

使用方法:
    python generate_video_txt.py [目录路径]

规则说明:
    - 支持使用{1}, {2}, {3}...等占位符
    - 自动识别文件名中的指定模式并提取内容
    - 支持自定义文案和标签配置
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple


def clean_filename(filename: str) -> str:
    """清理文件名，移除扩展名"""
    return os.path.splitext(filename)[0]


def parse_pattern(filename: str, pattern_prefix: str = None) -> List[str]:
    """
    解析文件名，提取用于替换的内容
    
    Args:
        filename: 原始文件名 (已清理扩展名)
        pattern_prefix: 用于识别的模式前缀格式，如 '单字模版_'
    
    Returns:
        提取的内容列表，用于填充{1},{2}等占位符
    """
    cleaned = clean_filename(filename)
    
    # 如果提供了模式前缀
    if pattern_prefix and cleaned.startswith(pattern_prefix):
        # 移除模式前缀
        content = cleaned[len(pattern_prefix):]
    else:
        # 如果没提供模式，按照下划线分割
        parts = cleaned.split('_')
        if len(parts) > 1 and parts[0].endswith('模版'):
            # 匹配 "xxx模版_内容" 的格式
            content = '_'.join(parts[1:]) if len(parts) > 1 else parts[0]
        else:
            # 如果没有模式，使用整个文件名作为{1}
            return [cleaned]
    
    # 进一步分割内容部分，支持多段提取
    if '_' in content:
        return content.split('_')
    else:
        return [content]


def replace_placeholders(template: str, values: List[str]) -> str:
    """
    替换模板中的{1}, {2}等占位符
    
    Args:
        template: 包含占位符的模板字符串
        values: 要替换的值的列表
    
    Returns:
        替换后的字符串
    """
    result = template
    for i, value in enumerate(values, 1):
        placeholder = f"{{{i}}}"
        result = result.replace(placeholder, value)
    
    # 移除未使用的占位符
    result = re.sub(r'\{\d+\}', '', result)
    
    return result.strip()


def check_pattern_format(filename: str) -> Tuple[bool, str]:
    """
    检查文件名是否符合特定模式格式
    
    Returns:
        (是否匹配, 模式前缀)
    """
    cleaned = clean_filename(filename)
    
    # 检查是否包含 "模版" 字样和对应的模式
    pattern = r'(.+模版)_(.+)'
    match = re.match(pattern, cleaned)
    
    if match:
        return True, match.group(1) + '_'
    
    # 检查下划线分割的格式
    if '_' in cleaned and cleaned.count('_') >= 1:
        parts = cleaned.split('_')
        if len(parts) >= 2:
            return True, parts[0] + '_'
    
    return False, ""


def hex_to_rgb(hex_color):
    """十六进制颜色转RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """RGB转十六进制颜色"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def process_mp4_files(directory: str) -> List[Path]:
    """遍历目录获取所有MP4文件"""
    directory_path = Path(directory)
    if not directory_path.exists():
        raise ValueError(f"目录不存在: {directory}")
    
    if not directory_path.is_dir():
        raise ValueError(f"路径不是目录: {directory}")
    
    return list(directory_path.glob("*.mp4"))


def get_user_input() -> Dict:
    """获取用户输入配置"""
    config = {
        'custom_copy': False,
        'copy_template': '',
        'use_tags': False,
        'tags': '',
        'pattern_prefix': None
    }
    
    print("=== 视频文案生成器 ===")
    print()
    
    # 是否使用自定义文案
    while True:
        custom_choice = input("是否要自定义文案？(y/N): ").strip().lower()
        if custom_choice in ['y', 'yes']:
            config['custom_copy'] = True
            break
        elif custom_choice in ['n', 'no', '']:
            config['custom_copy'] = False
            break
        else:
            print("请输入 y 或 n")
    
    if config['custom_copy']:
        print()
        print("📋 文案模式说明:")
        print("   使用 {1}, {2}, {3}... 作为占位符")
        print("   例如：文件名 '单字模版_荒.mp4'")
        print("   模板 '楷书必练字<{1}>' 将生成 '楷书必练字<荒>'")
        print()
        
        print("✏️  常见模板示例:")
        print("   1. 楷书必练字<{1}>")
        print("   2. {1}字练习本")
        print("   3. {1}字基础教程")
        print("   4. {1}字难点详解了")
        print()
        
        config['copy_template'] = input("请输入文案模板: ").strip()
        
        # 提示输入模式前缀（可选）
        print()
        pattern_input = input("请输入模式前缀格式（例如：'单字模版_'，直接回车跳过）: ").strip()
        if pattern_input:
            config['pattern_prefix'] = pattern_input
    
    # 是否添加标签
    print()
    while True:
        tags_choice = input("是否需要输出标签？(y/N): ").strip().lower()
        if tags_choice in ['y', 'yes']:
            config['use_tags'] = True
            tags = input("请输入标签（例如：#书法#楷书 或 书法,楷书）: ").strip()
            
            # 处理标签格式
            if '#' in tags:
                # 保持原有的#标签格式
                config['tags'] = tags
            else:
                # 转换为#标签格式
                tag_parts = [t.strip() for t in tags.split('#') if t.strip()]
                if not tags.startswith('#'):
                    tag_parts = [t for part in tags.split(',') for t in part.strip().split('#') if t.strip()]
                    if tag_parts:
                        config['tags'] = '#' + '#'.join(tag_parts)
                    else:
                        config['tags'] = tags
                else:
                    config['tags'] = tags
                    
            break
        elif tags_choice in ['n', 'no', '']:
            config['use_tags'] = False
            break
        else:
            print("请输入 y 或 n")
    
    return config


def generate_txt_content(filename: str, config: Dict) -> str:
    """基于配置生成txt文件内容"""
    print(f"processing file: {filename}")
    
    # 检查文件名格式并提取模式
    has_pattern, pattern_prefix = check_pattern_format(filename)
    
    if has_pattern and not config.get('pattern_prefix'):
        config['pattern_prefix'] = pattern_prefix
    
    # 解析占位符值
    placeholder_values = parse_pattern(filename, config.get('pattern_prefix'))
    
    # 生成内容
    content_parts = []
    
    if config['custom_copy']:
        # 使用自定义文案模板
        copy_text = replace_placeholders(config['copy_template'], placeholder_values)
        content_parts.append(copy_text)
    else:
        # 默认文案
        if len(placeholder_values) >= 1:
            content_parts.append(f"视频内容: {placeholder_values[0]}")
        else:
            content_parts.append(f"视频内容: {clean_filename(filename)}")
    
    if config['use_tags']:
        content_parts.append(f"{config['tags']}")
    
    return '\n'.join(content_parts)


def process_directory(directory: str, config: Dict):
    """处理整个目录"""
    try:
        mp4_files = process_mp4_files(directory)
        
        if not mp4_files:
            print(f"❌ 在目录 '{directory}' 中未找到MP4文件")
            return
        
        print(f"📁 找到 {len(mp4_files)} 个MP4文件")
        print()
        
        generated_files = 0
        
        for mp4_file in sorted(mp4_files):
            filename = mp4_file.name
            txt_filename = mp4_file.with_suffix('.txt')
            
            # 生成内容
            content = generate_txt_content(filename, config)
            
            # 写入文件
            try:
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 生成: {txt_filename.name}")
                print(f"   内容: {content}")
                
                generated_files += 1
                
            except Exception as e:
                print(f"❌ 写入文件失败 {txt_filename.name}: {e}")
        
        print()
        print(f"🎉 处理完成！共生成 {generated_files} 个.txt文件")
        
    except Exception as e:
        print(f"❌ 处理目录时出错: {e}")


def main():
    """主函数"""
    if len(sys.argv) > 2:
        print("使用方法: python generate_video_txt.py [目录路径]")
        return
    
    # 获取目录路径
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    else:
        directory = input("请输入要处理的目录路径（直接回车使用当前目录）: ").strip()
        if not directory:
            directory = "."
    
    # 用户配置
    config = get_user_input()
    
    # 处理目录
    process_directory(directory, config)


if __name__ == "__main__":
    main()