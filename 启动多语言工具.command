#!/bin/bash
# VideoTranslator v1.0

cd "$(dirname "$0")"

echo "======================================"
echo "🎬 VideoTranslator v1.0"
echo "======================================"
echo ""

# 确定Python路径
if [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
    echo "✅ 使用虚拟环境"
else
    PYTHON="python3"
    echo "⚠️  使用系统Python"
fi

echo ""

# 检查whisper
if $PYTHON -c "import whisper" 2>/dev/null; then
    echo "✅ Whisper已安装"
elif $PYTHON -c "import faster_whisper" 2>/dev/null; then
    echo "✅ Faster-Whisper已安装"
else
    echo "❌ Whisper未安装"
    echo "   安装命令: $PYTHON -m pip install openai-whisper"
fi

# 检查转录模块
if $PYTHON -c "from s1_transcribe import extract_subtitles" 2>/dev/null; then
    echo "✅ 转录模块可用"
else
    echo "⚠️  转录模块不可用"
fi

echo ""
echo "正在启动..."
echo "======================================"
echo ""

# 清理缓存
rm -rf __pycache__ 2>/dev/null

# 启动GUI（优先使用v1版本）
if [ -f "gui_app_v1.py" ]; then
    $PYTHON gui_app_v1.py
else
    $PYTHON gui_app_multilang_turbo.py
fi

echo ""
echo "程序已关闭"

