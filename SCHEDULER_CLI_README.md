# 多平台视频调度发布器 - 命令行参数使用说明

## 概述

`multi_platform_video_scheduler_final.py` 现已支持命令行参数配置，可以在运行时直接设置发布时间等参数，无需修改代码。

## 基本用法

### 1. 使用默认配置运行
```bash
python multi_platform_video_scheduler_final.py
```

### 2. 设置发布时间
```bash
# 设置单一发布时间（每天9点发布）
python multi_platform_video_scheduler_final.py --times '[9]'

# 设置多个发布时间（每天9点、15点、20点发布）
python multi_platform_video_scheduler_final.py --times '9,15,20'

# 使用默认发布时间 [5, 8, 12, 17, 19]
python multi_platform_video_scheduler_final.py
```

### 3. 设置其他参数
```bash
# 设置分组大小为3
python multi_platform_video_scheduler_final.py --group-size 3

# 设置随机时间偏移为5分钟
python multi_platform_video_scheduler_final.py --random-minutes 5

# 设置开始日期
python multi_platform_video_scheduler_final.py --start-date 2025-10-01

# 设置开始天数偏移
python multi_platform_video_scheduler_final.py --start-days 2
```

### 4. 组合使用参数
```bash
# 同时设置发布时间和分组大小
python multi_platform_video_scheduler_final.py --times '[9]' --group-size 3

# 设置发布时间、开始日期和随机偏移
python multi_platform_video_scheduler_final.py --times '9,15,20' --start-date 2025-10-01 --random-minutes 5

# 完整配置示例
python multi_platform_video_scheduler_final.py --times '[9]' --group-size 4 --random-minutes 8 --start-date 2025-11-01
```

## 支持的参数

| 参数 | 短参数 | 描述 | 默认值 | 示例 |
|------|--------|------|--------|------|
| `--times` | `-t` | 设置发布时间 | [5, 8, 12, 17, 19] | `--times '[9]'` |
| `--start-date` | `-d` | 设置开始日期 | 明天 | `--start-date 2025-10-01` |
| `--group-size` | `-gs` | 设置分组大小 | 5 | `--group-size 3` |
| `--random-minutes` | `-rm` | 设置随机时间偏移 | 10 | `--random-minutes 5` |
| `--start-days` | `-sd` | 设置开始天数偏移 | 0 | `--start-days 2` |
| `--version` | `-v` | 显示版本信息 | - | `--version` |
| `--help` | `-h` | 显示帮助信息 | - | `--help` |

## 发布时间格式

支持多种格式：

### 格式1: 方括号格式
```bash
--times '[9]'        # 每天9点发布
--times '[10,15]'    # 每天10点和15点发布
```

### 格式2: 逗号分隔
```bash
--times '9,15,20'    # 每天9点、15点、20点发布
--times '5,8,12,17,19'  # 每天5点、8点、12点、17点、19点发布
```

### 格式3: 空格分隔
```bash
--times '9 15 20'    # 每天9点、15点、20点发布
```

## 使用示例

### 示例1: 简单单点发布
```bash
# 每天9点发布，其他参数使用默认值
python multi_platform_video_scheduler_final.py --times '[9]'
```

### 示例2: 多点发布
```bash
# 每天9点、15点、20点发布，分组大小为3
python multi_platform_video_scheduler_final.py --times '9,15,20' --group-size 3
```

### 示例3: 完整配置
```bash
# 完整配置：发布时间、开始日期、分组大小、随机偏移
python multi_platform_video_scheduler_final.py \
  --times '[9]' \
  --start-date 2025-10-01 \
  --group-size 4 \
  --random-minutes 8
```

### 示例4: 查看帮助
```bash
# 查看完整的帮助信息
python multi_platform_video_scheduler_final.py --help
```

## 默认配置

如果不指定任何参数，将使用以下默认配置：

- **发布时间**: [5, 8, 12, 17, 19] (每天5点、8点、12点、17点、19点)
- **分组大小**: 5
- **随机时间偏移**: 10分钟 (0-10分钟随机偏移)
- **开始日期**: 明天
- **开始天数偏移**: 0

## 注意事项

1. **时间格式**: 发布时间使用24小时制，范围0-23
2. **日期格式**: 开始日期格式为 YYYY-MM-DD
3. **分组大小**: 必须为正整数
4. **随机偏移**: 必须为非负整数
5. **参数优先级**: 命令行参数优先于默认配置

## 错误处理

脚本会自动验证参数的有效性：

- 无效的时间格式会显示错误信息并退出
- 无效的日期格式会显示错误信息并退出
- 无效的数值参数会显示错误信息并退出
- 参数解析失败会显示使用提示

## 兼容性

- 完全兼容原有的交互式模式
- 命令行参数为可选功能
- 原有配置文件和功能不受影响