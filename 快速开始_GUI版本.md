# 🚀 VideoTranslator - 快速开始

## 第一步：安装依赖

### ⚠️ 重要提示

如果遇到 `externally-managed-environment` 错误，说明您需要使用**虚拟环境**。

### 方法1：使用项目虚拟环境（推荐） ⭐

项目中已经有虚拟环境，直接激活使用：

```bash
# 进入项目目录
cd /Users/admin/Desktop/video_tool/video_reposting

# 激活虚拟环境
source venv/bin/activate

# 安装GUI依赖
pip install PyQt6

# 启动应用
python gui_app.py
```

### 方法2：创建新的虚拟环境

如果上面的虚拟环境有问题，创建新的：

```bash
# 进入项目目录
cd /Users/admin/Desktop/video_tool/video_reposting

# 创建虚拟环境
python3 -m venv venv_gui

# 激活虚拟环境
source venv_gui/bin/activate

# 安装所有依赖
pip install -r requirements.txt
pip install PyQt6

# 启动应用
python gui_app.py
```

### 方法3：如果遇到SSL错误，使用国内镜像

```bash
# 激活虚拟环境后
source venv/bin/activate

# 使用清华镜像源安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt6
```

### 验证安装

运行以下命令测试PyQt6是否安装成功：

```bash
python3 -c "from PyQt6.QtWidgets import QApplication; print('✅ PyQt6安装成功！')"
```

如果看到"✅ PyQt6安装成功！"，说明安装完成。

## 第二步：启动应用

### 方法1：使用启动脚本（最简单）

```bash
# 双击运行或在终端执行
./启动GUI.sh
```

### 方法2：直接运行Python脚本

```bash
python3 gui_app.py
```

## 第三步：开始使用

1. **拖拽或选择视频文件**
   - 将视频文件拖到窗口顶部的拖拽区域
   - 或点击拖拽区域选择文件

2. **配置处理参数**
   - 选择目标语言（如：中文、英文、日文等）
   - 选择配音音色（根据语言自动显示可用选项）
   - 选择字幕位置（底部/顶部/中间）
   - 调整字幕边距

3. **开始处理**
   - 点击"🚀 开始处理"按钮
   - 等待处理完成（可在日志窗口查看进度）
   - 处理完成后会弹出提示窗口

4. **查看结果**
   - 点击"📁 打开输出文件夹"
   - 在Finder中查看生成的视频和文件

## 常见问题解决

### Q1: 提示"No module named 'PyQt6'"

**解决方案**：
```bash
pip3 install PyQt6
```

### Q2: 提示"command not found: python3"

**解决方案**：
```bash
# 安装Python 3
brew install python@3.11
```

### Q3: 提示"ffmpeg not found"

**解决方案**：
```bash
# 安装FFmpeg
brew install ffmpeg

# 验证安装
ffmpeg -version
```

### Q4: SSL证书错误

**解决方案**：使用国内镜像源
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt6
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### Q5: 权限错误

**解决方案**：
```bash
# 给启动脚本添加执行权限
chmod +x 启动GUI.sh
```

## 系统要求

- ✅ macOS 10.15 或更高版本
- ✅ Python 3.8 或更高版本
- ✅ 至少 8GB 内存
- ✅ FFmpeg（用于视频处理）

## 检查系统环境

运行以下命令检查您的系统是否满足要求：

```bash
# 检查Python版本
python3 --version

# 检查FFmpeg
ffmpeg -version

# 检查PyQt6
python3 -c "from PyQt6.QtWidgets import QApplication; print('PyQt6: ✅')"

# 检查其他依赖
python3 -c "import whisper; print('Whisper: ✅')"
python3 -c "import edge_tts; print('Edge-TTS: ✅')"
```

如果所有检查都通过，您就可以开始使用了！

## 完整安装流程（适合新手）

```bash
# 1. 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装Python和FFmpeg
brew install python@3.11 ffmpeg

# 3. 进入项目目录
cd /Users/admin/Desktop/video_tool/video_reposting

# 4. 安装Python依赖
pip3 install -r requirements.txt
pip3 install PyQt6

# 5. 启动应用
python3 gui_app.py
```

## 下一步

查看完整文档：[README_GUI.md](README_GUI.md)

## 技术支持

如果遇到问题：

1. 首先查看应用日志窗口的错误信息
2. 检查是否所有依赖都已正确安装
3. 确保FFmpeg可以正常运行

祝您使用愉快！🎉

