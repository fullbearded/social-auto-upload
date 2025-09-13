# 快手数据统计使用指南

## 🚀 新设计的 Statistics 目录结构

我已按照 Uploader 目录结构重新设计了统计功能：

```
statistics/
├── kuaishou_uploader/           # 快手统计数据获取套件
│   ├── __init__.py
│   ├── main.py                 # 主接口类
│   ├── kuashou_scraper.py       # 数据爬取器
│   └── stats_models.py          # 数据模型定义
├── statistics_cli.py           # 统一CLI工具
└── [其他平台统计套件]          # 预留扩展
```

## 📊 使用方式

### 方法 1：直接调用 (最简单)

```bash
python get_kuaishou_stats_fixed.py
```

### 方法 2：通过 CLI 工具

```bash
# 检查平台支持状态
python statistics/statistics_cli.py list

# 检查Cookie状态
python statistics/statistics_cli.py check kuaishou

# 获取数据
python statistics/statistics_cli.py get kuaishou --output reports

# 详细分析
python statistics/statistics_cli.py get kuaishou --format all
```

### 方法 3：代码调用

```python
# 快速获取
import asyncio
from statistics.kuaishou_uploader import get_kuaishou_statistics

async def demo():
    data = await get_kuaishou_statistics("path/to/cookie.json")
    print(f"账号：{data['account_info']['account_name']}")

asyncio.run(demo())
```

## 📋 数据结构

### 账号概览数据

```json
{
  "account_name": "快手账号",
  "total_videos": 150,
  "total_views": 1250000,
  "total_likes": 89500,
  "followers": 8750,
  ...
}
```

### 视频详情数据

```json
{
  "video_id": "ks_123456",
  "title": "今日分享...",
  "views": 12500,
  "likes": 850,
  "comments": 125,
  "like_rate": 6.8
}
```

## 🎯 支持的数据

**来源于：https://cp.kuaishou.com/statistics/works**

✅ 账号总览数据

- 粉丝数量
- 视频总数
- 总播放量
- 总互动量

✅ 视频详情数据

- 每条视频的播放量
- 点赞、评论、分享数
- 互动率计算
- 上传时间信息

✅ 质量评估

- 互动质量评分
- 内容评分
- 账号健康评分

## 🔧 先决条件

1. **在正确位置有 Cookie 文件**

   ```
   cookies/ks_uploader/account.json
   ```

2. **安装 Playwright 浏览器**

   ```bash
   playwright install chromium
   ```

3. **获取 Cookie**（如不存在）
   ```bash
   python examples/get_ks_cookie.py
   ```

## 🐛 故障排除

**Cookie 验证失败：**

```bash
python statistics/statistics_cli.py check kuaishou
```

**模块导入错误：**
确保项目根目录在 Python 路径中，或使用完整路径。

**网络问题：**
检查网络连接，如需代理配置请在代码中设置。
