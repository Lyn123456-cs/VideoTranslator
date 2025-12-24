#!/bin/bash
# 创建增量更新包 - 只包含必要的更新文件

cd "$(dirname "$0")"

echo "======================================"
echo "📦 创建 VideoTranslator 更新包"
echo "======================================"
echo ""

# 更新版本号
NEW_VERSION="v1.1_$(date +%Y%m%d)"
UPDATE_DIR="VideoTranslator_Update_${NEW_VERSION}"

echo "创建版本: $NEW_VERSION"
echo ""

# 创建更新目录
rm -rf "$UPDATE_DIR"
mkdir -p "$UPDATE_DIR"

# 1. 核心文件（必须）
echo "📋 收集核心文件..."
cp gui_app.py "$UPDATE_DIR/" 2>/dev/null
cp gui_app_v1.py "$UPDATE_DIR/" 2>/dev/null
cp video_processor.py "$UPDATE_DIR/" 2>/dev/null
cp config_manager.py "$UPDATE_DIR/" 2>/dev/null
cp multilang_fast_parallel.py "$UPDATE_DIR/" 2>/dev/null

# 2. 处理脚本（必须）
echo "📋 收集处理脚本..."
cp s1_transcribe.py "$UPDATE_DIR/" 2>/dev/null
cp s2_translate.py "$UPDATE_DIR/" 2>/dev/null
cp s3_generate_voiceover.py "$UPDATE_DIR/" 2>/dev/null
cp s5_burn_subtitles_simple.py "$UPDATE_DIR/" 2>/dev/null

# 3. 启动脚本
echo "📋 收集启动脚本..."
cp 启动多语言工具.command "$UPDATE_DIR/" 2>/dev/null
cp 启动TurboGUI.command "$UPDATE_DIR/" 2>/dev/null
cp 启动GUI.command "$UPDATE_DIR/" 2>/dev/null
cp 一键启动.sh "$UPDATE_DIR/" 2>/dev/null

# 4. 兼容补丁（如果用户是Python 3.14）
echo "📋 收集兼容补丁..."
mkdir -p "$UPDATE_DIR/patches"
cp venv/lib/python3.14/site-packages/cgi.py "$UPDATE_DIR/patches/" 2>/dev/null
cp venv/lib/python3.14/site-packages/audioop.py "$UPDATE_DIR/patches/" 2>/dev/null

# 5. 文档
echo "📋 收集文档..."
cp README_GUI.md "$UPDATE_DIR/" 2>/dev/null
cp 快速开始_GUI版本.md "$UPDATE_DIR/" 2>/dev/null
cp 多语言工具更新日志.md "$UPDATE_DIR/" 2>/dev/null
cp 更新说明_简化版本.md "$UPDATE_DIR/" 2>/dev/null

# 6. 创建更新说明
cat > "$UPDATE_DIR/更新说明.txt" << 'EOF'
====================================
VideoTranslator 更新包
====================================

本次更新内容：
✅ 工具名称统一为 VideoTranslator
✅ 语言列表扩展到16种
✅ 印地语改为印度语
✅ 智能TTS引擎（Edge + gTTS自动降级）
✅ 修复Python 3.14兼容性问题
✅ 优化进度显示
✅ 添加字幕预览功能

安装步骤：
1. 备份您的旧版本（可选）
2. 将本更新包中的文件复制到项目目录，覆盖旧文件
3. 如果使用Python 3.14，复制patches文件夹中的内容到：
   venv/lib/python3.14/site-packages/
4. 运行：./启动多语言工具.command

注意事项：
- 不会影响您已有的视频和配置
- 配置文件会自动迁移到新位置
- 虚拟环境(venv)不需要重新创建

更新时间：$(date +%Y-%m-%d)
版本：${NEW_VERSION}
EOF

# 7. 创建应用更新脚本
cat > "$UPDATE_DIR/应用更新.sh" << 'EOF'
#!/bin/bash
# 应用更新脚本

cd "$(dirname "$0")"

echo "======================================"
echo "📦 应用 VideoTranslator 更新"
echo "======================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "../gui_app.py" ] && [ ! -f "../gui_app_v1.py" ]; then
    echo "❌ 错误：请将此更新包放在VideoTranslator项目目录中"
    echo "   应该在项目根目录看到 gui_app.py 或 gui_app_v1.py"
    exit 1
fi

echo "🔍 检测到项目目录"
echo ""

# 备份旧版本（可选）
read -p "是否备份旧版本？(y/n) [默认: y]: " BACKUP
BACKUP=${BACKUP:-y}

if [ "$BACKUP" = "y" ]; then
    BACKUP_DIR="../backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 创建备份: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # 备份核心文件
    cp ../gui_app*.py "$BACKUP_DIR/" 2>/dev/null
    cp ../*.py "$BACKUP_DIR/" 2>/dev/null
    cp ../*.command "$BACKUP_DIR/" 2>/dev/null
    cp ../*.sh "$BACKUP_DIR/" 2>/dev/null
    
    echo "✅ 备份完成"
    echo ""
fi

# 应用更新
echo "📦 正在更新文件..."
cp -v *.py ../ 2>/dev/null
cp -v *.command ../ 2>/dev/null
cp -v *.sh ../ 2>/dev/null
cp -v *.md ../ 2>/dev/null

# 设置执行权限
chmod +x ../*.command 2>/dev/null
chmod +x ../*.sh 2>/dev/null

echo ""
echo "✅ 更新完成！"
echo ""
echo "📝 后续步骤："
echo "  1. 阅读 更新说明.txt 了解变更内容"
echo "  2. 运行: ../启动多语言工具.command"
echo ""

read -p "按回车键退出..."
EOF

chmod +x "$UPDATE_DIR/应用更新.sh"

# 8. 打包
echo ""
echo "🗜️  创建压缩包..."
zip -r "${UPDATE_DIR}.zip" "$UPDATE_DIR"

# 计算大小
SIZE=$(du -h "${UPDATE_DIR}.zip" | cut -f1)

echo ""
echo "======================================"
echo "✅ 更新包创建完成！"
echo "======================================"
echo ""
echo "📦 文件: ${UPDATE_DIR}.zip"
echo "📊 大小: $SIZE"
echo ""
echo "📤 分发方式："
echo "  1. 发送 ${UPDATE_DIR}.zip 给业务同学"
echo "  2. 他们解压后运行 ./应用更新.sh"
echo "  3. 更新完成，重启工具即可"
echo ""
echo "💡 提示："
echo "  - 更新包只有几百KB（不包含依赖库）"
echo "  - 用户的venv和数据不会被影响"
echo "  - 可以通过微信/邮件/网盘分发"
echo ""
