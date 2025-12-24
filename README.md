# 🎬 VideoTranslator

> 专业的视频多语言本地化工具 - 支持16种语言的自动字幕提取、翻译和配音

[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/你的用户名/VideoTranslator/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ 功能特性

- 🎯 **自动字幕提取** - 基于Whisper AI，支持自动语言识别
- 🌍 **16种语言翻译** - 中文、英语、日语、韩语、法语、德语、西语、葡语、俄语等
- 🎙️ **智能配音生成** - Edge TTS高质量配音 + gTTS稳定备份
- ⚡ **并行处理** - 同时处理多种语言，速度提升3-5倍
- 🎨 **现代化GUI** - 基于PyQt6的友好界面
- 📊 **实时进度显示** - 处理过程可视化
- 🔊 **音量标准化** - 自动优化音频输出

## 🎯 使用场景

| 场景 | 说明 |
|------|------|
| 📱 **内容出海** | 将中文视频翻译成多种语言 |
| 🌏 **内容引入** | 将国外视频本地化为中文 |
| 📹 **批量本地化** | 一个视频同时生成多语言版本 |
| 🎓 **教育培训** | 教程视频多语言化 |

## 📦 下载安装

### 方式1：下载打包版本（推荐）⭐

前往 [Releases](https://github.com/你的用户名/VideoTranslator/releases) 页面下载：

- **Mac用户**: `VideoTranslator_macOS.zip`
- **Windows用户**: `VideoTranslator_Windows.zip`

#### Mac安装步骤

```bash
# 1. 解压下载的文件
unzip VideoTranslator_macOS.zip

# 2. 拖拽到应用程序文件夹（或直接双击运行）

# 3. 安装FFmpeg（一次性）
brew install ffmpeg

# 4. 启动应用
# 在启动台或应用程序文件夹找到VideoTranslator
```

#### Windows安装步骤

```
1. 解压下载的文件
2. 安装FFmpeg（参考压缩包内说明）
3. 双击 VideoTranslator.exe 启动
```

---

### 方式2：从源码运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/VideoTranslator.git
cd VideoTranslator

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install PyQt6

# 安装FFmpeg
# Mac: brew install ffmpeg
# Windows: 参考 https://ffmpeg.org/download.html

# 运行应用
python gui_app_v1.py
```

## 🚀 快速开始

### 1. 启动应用

双击打开VideoTranslator

### 2. 选择视频

点击"选择视频"或拖拽视频文件

### 3. 选择目标语言

从下拉菜单选择要翻译的语言

### 4. 开始处理

点击"开始处理"，等待完成

### 5. 获取结果

生成的文件在视频同目录下：
- `xxx_final.mp4` - 最终视频
- `xxx_en.srt` - 翻译后字幕
- `xxx_en_voiceover.mp3` - 配音文件

## 🌍 支持的语言

<table>
<tr>
<td>🇨🇳 中文</td>
<td>🇺🇸 英语</td>
<td>🇯🇵 日语</td>
<td>🇰🇷 韩语</td>
</tr>
<tr>
<td>🇫🇷 法语</td>
<td>🇩🇪 德语</td>
<td>🇪🇸 西班牙语</td>
<td>🇵🇹 葡萄牙语</td>
</tr>
<tr>
<td>🇷🇺 俄语</td>
<td>🇸🇦 阿拉伯语</td>
<td>🇮🇳 印度语</td>
<td>🇹🇭 泰语</td>
</tr>
<tr>
<td>🇻🇳 越南语</td>
<td>🇮🇹 意大利语</td>
<td>🇹🇷 土耳其语</td>
<td>🇮🇩 印尼语</td>
</tr>
</table>

## 🛠️ 技术栈

- **GUI**: PyQt6
- **AI模型**: OpenAI Whisper / Faster-Whisper
- **翻译**: Google Translate
- **TTS**: Microsoft Edge TTS + Google TTS
- **视频处理**: FFmpeg
- **编程语言**: Python 3.11+

## 📚 详细文档

- [用户使用指南](README_GUI.md) - 详细的功能说明和使用教程
- [快速开始指南](快速开始_GUI版本.md) - 新手入门教程

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境

```bash
# 克隆项目
git clone https://github.com/你的用户名/VideoTranslator.git

# 安装开发依赖
pip install -r requirements.txt
pip install PyQt6

# 运行测试
python gui_app_v1.py
```

## 📄 开源协议

本项目采用 [MIT License](LICENSE)

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - 加速版Whisper
- [Edge TTS](https://github.com/rany2/edge-tts) - 高质量TTS
- [gTTS](https://github.com/pndurette/gTTS) - Google TTS
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [FFmpeg](https://ffmpeg.org/) - 视频处理

## ❓ 常见问题

### Q: 首次运行很慢？
A: 第一次使用时需要下载Whisper模型（约150MB），之后会很快。

### Q: Mac提示"无法验证开发者"？
A: 在"系统偏好设置" → "安全性与隐私"中点击"仍要打开"。

### Q: Windows提示"Windows已保护你的电脑"？
A: 点击"更多信息" → "仍要运行"。

### Q: 配音质量不好？
A: 工具会自动选择最佳TTS引擎（Edge TTS优先，失败时自动切换到gTTS）。

## 📧 联系方式

- 问题反馈: [GitHub Issues](https://github.com/你的用户名/VideoTranslator/issues)
- 邮件: your.email@example.com

---

**VideoTranslator** - 让视频跨越语言的边界 🌍

**版本**: v1.0  
**更新时间**: 2024-12-18
