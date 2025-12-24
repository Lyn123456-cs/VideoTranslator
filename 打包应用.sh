#!/bin/bash
# 打包成独立 macOS 应用（.app）
# 用户双击即可使用，无需安装任何依赖

set -e

echo "============================================"
echo "📦 打包 VideoTranslator 为独立应用"
echo "============================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 未找到虚拟环境，请先运行: ./自动安装依赖.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 PyInstaller
echo "📦 检查 PyInstaller..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "正在安装 PyInstaller..."
    pip install pyinstaller --quiet
    echo "✅ PyInstaller 安装完成"
else
    echo "✅ PyInstaller 已安装"
fi

# 清理旧文件
echo ""
echo "🧹 清理旧文件..."
rm -rf build dist *.spec

# 创建图标（如果不存在）
if [ ! -f "icon.icns" ]; then
    echo "⚠️  未找到 icon.icns，使用默认图标"
    ICON_FLAG=""
else
    ICON_FLAG="--icon=icon.icns"
fi

# 打包应用
echo ""
echo "📦 正在打包应用（需要几分钟）..."
echo ""

pyinstaller \
    --name="VideoTranslator" \
    --windowed \
    $ICON_FLAG \
    --add-data="s1_transcribe.py:." \
    --add-data="s2_translate.py:." \
    --add-data="s3_generate_voiceover.py:." \
    --add-data="s5_burn_subtitles_simple.py:." \
    --add-data="s6_remove_subtitle.py:." \
    --add-data="s7_clean_metadata.py:." \
    --add-data="video_processor.py:." \
    --add-data="config_manager.py:." \
    --add-data="multilang_fast_parallel.py:." \
    --add-data="README_GUI.md:." \
    --hidden-import=faster_whisper \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=edge_tts \
    --hidden-import=gtts \
    --hidden-import=googletrans \
    --hidden-import=srt \
    --hidden-import=pydub \
    --collect-all=faster_whisper \
    --collect-all=whisper \
    --collect-all=edge_tts \
    --collect-all=gtts \
    gui_app_v1.py

# 检查是否成功
if [ -d "dist/VideoTranslator.app" ]; then
    echo ""
    echo "============================================"
    echo "✅ Mac版本打包完成！"
    echo "============================================"
    echo ""
    echo "📂 应用位置: dist/VideoTranslator.app"
    echo ""
    
    # 获取应用大小
    APP_SIZE=$(du -sh "dist/VideoTranslator.app" | cut -f1)
    echo "📊 应用大小: $APP_SIZE"
    echo ""
    
    # 创建DMG镜像（可选）
    echo "🗜️  创建DMG镜像..."
    hdiutil create -volname "VideoTranslator" -srcfolder "dist/VideoTranslator.app" -ov -format UDZO "dist/VideoTranslator_macOS.dmg"
    
    if [ -f "dist/VideoTranslator_macOS.dmg" ]; then
        DMG_SIZE=$(du -sh "dist/VideoTranslator_macOS.dmg" | cut -f1)
        echo "✅ DMG创建完成: dist/VideoTranslator_macOS.dmg ($DMG_SIZE)"
    fi
    
    echo ""
    echo "🚀 使用方法："
    echo "  1. 双击运行: dist/VideoTranslator.app"
    echo "  2. 或拖到应用程序文件夹"
    echo "  3. 分发DMG文件给其他Mac用户"
    echo ""
    
    echo "💡 提示："
    echo "  - 用户双击即可使用，无需安装Python依赖"
    echo "  - 应用已包含所有Python库和模型"
    echo "  - ⚠️  用户仍需安装 ffmpeg（系统依赖）"
    echo "    Mac安装: brew install ffmpeg"
    echo ""
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi

# 退出虚拟环境
deactivate 2>/dev/null || true


