# 视频发布计划配置工具使用说明

## 概述

这个工具用于配置和管理视频的发布计划，支持设置发布时间、视频数量、分组大小等参数。

## 基本用法

### 1. 显示当前配置
```bash
python schedule_config.py --show
```

### 2. 修改发布时间
```bash
# 设置单一发布时间（每天9点发布）
python schedule_config.py --times '[9]'

# 设置多个发布时间（每天9点、15点、20点发布）
python schedule_config.py --times '9,15,20'
```

### 3. 修改其他配置
```bash
# 设置视频总数为10个
python schedule_config.py --total-videos 10

# 设置开始日期
python schedule_config.py --start-date 2025-10-01

# 设置分组大小
python schedule_config.py --group-size 3

# 设置随机时间偏移
python schedule_config.py --random-minutes 5
```

### 4. 生成发布计划
```bash
python schedule_config.py --generate
```

### 5. 组合使用
```bash
# 同时修改多个配置并显示结果
python schedule_config.py --times '[9]' --total-videos 8 --show
```

## 配置文件说明

工具会自动创建和管理 `schedule_config.json` 配置文件，包含以下参数：

- `start_date`: 开始日期
- `total_videos`: 视频总数
- `publish_days`: 发布天数
- `daily_times`: 每天发布时间（数组，24小时制）
- `group_size`: 分组大小
- `random_minutes`: 随机时间偏移（0-n分钟）
- `start_days_offset`: 开始天数偏移

## 发布时间格式

支持多种格式：
- `[9]` - 每天9点发布
- `9,15,20` - 每天9点、15点、20点发布
- `5,8,12,17,19` - 每天5点、8点、12点、17点、19点发布

## 示例输出

```
=== 📋 当前发布计划配置 ===
📅 开始日期: 2025-09-15
📹 视频总数: 5
📊 发布天数: 1
⏰ 发布时间: [9]
🎲 分组大小: 5
⏱️  随机时间偏移: 0-10分钟
📅 开始天数偏移: 0
```

## 高级功能

### 生成详细计划
使用 `--generate` 参数可以生成详细的发布计划，包括：
- 智能调度计划摘要
- 每日详细计划
- 随机分组结果
- 具体发布时间

### 使用不同配置文件
```bash
# 使用自定义配置文件
python schedule_config.py --config my_config.json --show
```

## 注意事项

1. 发布时间使用24小时制（0-23）
2. 视频文件会被随机分组并分配到不同的发布时间
3. 发布时间会添加随机偏移（0-配置的分钟数）以避免过于规律
4. 配置修改后自动保存到JSON文件

## 故障排除

如果遇到问题，可以：
1. 检查时间格式是否正确
2. 确保JSON配置文件格式正确
3. 使用 `--show` 参数查看当前配置
4. 检查是否有权限写入配置文件