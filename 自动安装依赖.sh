#!/bin/bash
# 视频本地化工具 - 自动安装脚本
# 使用方法：./自动安装依赖.sh

set -e  # 遇到错误立即退出

echo "============================================"
echo "🎬 视频多语言本地化工具 - 自动安装"
echo "============================================"
echo ""

# 检测操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅支持 macOS"
    exit 1
fi

# 检测 Python 版本
echo "📦 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 检测 Homebrew
echo ""
echo "📦 检查 Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "❌ 未找到 Homebrew"
    echo "正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew 已安装"
fi

# 修复 Homebrew 权限
echo ""
echo "🔧 修复 Homebrew 权限..."
if [ -d "/opt/homebrew" ]; then
    sudo chown -R $(whoami) /opt/homebrew 2>/dev/null || true
    echo "✅ 权限已修复"
fi

# 检测并安装 pkg-config
echo ""
echo "📦 检查 pkg-config..."
if ! command -v pkg-config &> /dev/null; then
    echo "正在安装 pkg-config..."
    brew install pkg-config
    echo "✅ pkg-config 安装完成"
else
    echo "✅ pkg-config 已安装"
fi

# 检测并安装 ffmpeg
echo ""
echo "📦 检查 ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "正在安装 ffmpeg..."
    brew install ffmpeg
    echo "✅ ffmpeg 安装完成"
else
    echo "✅ ffmpeg 已安装"
fi

# 创建虚拟环境（如果不存在）
echo ""
echo "🐍 设置 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "📦 安装 Python 依赖..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip --quiet

# 安装基础依赖
echo "安装基础依赖..."
pip install -r requirements.txt --quiet
pip install -r requirements_gui.txt --quiet

# 安装 gTTS（备用 TTS）
echo "安装 gTTS..."
pip install gtts --quiet

# 直接安装 Faster-Whisper（免费且更快）
echo ""
echo "⚡ 安装 Faster-Whisper（语音识别速度快 5 倍，完全免费）"
pip install faster-whisper --quiet

# 自动替换脚本为 Faster-Whisper 版本
if [ -f "s1_transcribe_faster.py" ]; then
    echo "正在切换到 Faster-Whisper 版本..."
    if [ ! -f "s1_transcribe_原版.py" ] && [ -f "s1_transcribe.py" ]; then
        cp s1_transcribe.py s1_transcribe_原版.py 2>/dev/null || true
    fi
    cp s1_transcribe_faster.py s1_transcribe.py
    echo "✅ Faster-Whisper 安装完成"
else
    echo "✅ Faster-Whisper 安装完成"
fi

# 完成
echo ""
echo "============================================"
echo "✅ 安装完成！"
echo "============================================"
echo ""
echo "🚀 启动方式："
echo "  GUI 版本:    python3 gui_app.py"
echo "  命令行版本:  python3 main.py"
echo ""
echo "📚 文档："
echo "  GUI 使用说明:       GUI版本说明.md"
echo "  快速开始:          QUICKSTART.md"
echo ""
echo "💡 提示："
echo "  - 所有依赖已安装在虚拟环境中"
echo "  - 重启终端后需要先激活虚拟环境: source venv/bin/activate"
echo "  - 或直接使用: python3 gui_app.py (会自动使用虚拟环境)"
echo ""


