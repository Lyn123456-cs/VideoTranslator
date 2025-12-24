#!/bin/bash
# 一键启动脚本 - 自动处理虚拟环境

cd "$(dirname "$0")"

echo "🎬 VideoTranslator - GUI版本"
echo "========================================"
echo ""

# 1. 激活虚拟环境
if [ -d "venv" ]; then
    echo "✅ 激活虚拟环境..."
    source venv/bin/activate
else
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "📦 安装基础依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 2. 检查并安装PyQt6
if ! python -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
    echo "📦 安装GUI依赖 (PyQt6)..."
    pip install PyQt6
    
    if [ $? -ne 0 ]; then
        echo "⚠️  常规安装失败，尝试使用国内镜像..."
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt6
    fi
fi

# 3. 启动应用
echo ""
echo "✅ 环境准备完成，正在启动应用..."
echo ""

python gui_app.py

# 应用关闭后的提示
echo ""
echo "👋 应用已关闭"

