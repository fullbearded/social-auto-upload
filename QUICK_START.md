# 🚀 多平台智能视频调度发布器 - 快速开始

## 1️⃣ 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 安装浏览器
playwright install chromium firefox

# 配置环境
cp conf.example.py conf.py
# 编辑conf.py，设置你的Chrome路径
```

## 2️⃣ 准备内容

```
# 创建目录结构
mkdir -p videos cookies

# 放入视频文件
videos/
├── video1.mp4
├── video2.mp4
└── ...

# 可选：添加封面（同名.png文件）
video1.mp4 → video1.png

# 可选：添加标题标签（同名.txt文件）
video1.mp4 → video1.txt
```

## 3️⃣ 生成Cookie

```bash
# 为需要的平台生成cookie
python examples/douyin_uploader/douyin_cookie.py
python examples/bilibili_uploader/bilibili_cookie.py
# ...其他平台
```

## 4️⃣ 运行发布器

```bash
python multi_platform_video_scheduler.py
```

## 5️⃣ 按提示操作

1. **选择平台**：输入平台编号，如 `1,2,3`
2. **确认计划**：查看发布时间表
3. **开始发布**：输入 `y` 确认执行

---

## 📱 平台选择指南

| 编号 | 平台 | 特点 |
|-----|-----|------|
| 1 | 抖音 | 支持自定义封面 |
| 2 | 哔哩哔哩 | 需要biliup库 |
| 3 | 小红书 | 支持地理位置 |
| 4 | 快手 | 限3个标签 |
| 5 | 百家号 | 支持AI成片 |
| 6 | 腾讯视频号 | 支持商品添加 |
| 7 | TikTok | 用Firefox浏览器 |
| 8 | 快手备用 | 功能类似 |

**示例输入**：
- `1,2` → 抖音+哔哩哔哩
- `1,3,5` → 抖音+小红书+百家号
- 直接回车 → 默认抖音+哔哩哔哩

---

## ⏰ 智能调度特性

- **发布时间**：6:00、9:00、12:00、17:00、19:00
- **随机偏移**：每个视频增加0-10分钟随机延迟
- **智能分组**：每5个视频一组，自动处理余数
- **动态规划**：根据视频数量自动计算天数

---

## 📊 使用示例

```bash
$ python multi_platform_video_scheduler.py

🚀 === 多平台智能视频调度发布器 === 🚀
🌐 支持8大主流平台 | ⏰ 智能时间调度 | 🎲 随机偏移
📋 详细说明: MULTI_PLATFORM_VIDEO_SCHEDULER_USAGE.md
============================================================

📱 请选择要发布的平台（输入平台编号，多个平台用逗号分隔）:
...

请选择平台: 1,2,3
✅ 已选择平台: 抖音(抖音), 哔哩哔哩(哔哩哔哩), 小红书(小红书)

📅 发布时间: ['6:00', '9:00', '12:00', '17:00', '19:00']
📊 每组视频: 5个
🚀 发布平台: 抖音(抖音), 哔哩哔哩(哔哩哔哩), 小红书(小红书)

📹 发现视频: 15个
...
🤔 确认执行发布计划？ (y/N): y

🚀 === 开始智能发布 === 🚀
...
🎉 === 多平台智能发布完成 === 🎉
```

---

## 🆘 常见问题

**Q: Cookie文件怎么生成？**
A: 运行各平台的示例脚本，如 `python examples/douyin_uploader/douyin_cookie.py`

**Q: 支持哪些视频格式？**
A: 主要支持 `.mp4` 格式，具体限制参考各平台要求

**Q: 可以同时发布到多个平台吗？**
A: 可以！支持同时发布到8个平台，系统会自动处理各平台的差异

**Q: 发布时间可以自定义吗？**
A: 可以！编辑脚本中的 `daily_publish_times` 变量

**Q: 随机偏移是什么？**
A: 在设定时间基础上增加0-10分钟随机延迟，让发布更自然

---

📖 **完整说明**: 查看 `MULTI_PLATFORM_VIDEO_SCHEDULER_USAGE.md`

🎉 **开始你的智能视频发布之旅！**