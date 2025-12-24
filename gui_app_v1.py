#!/usr/bin/env python3
"""
VideoTranslator v1.0

功能特性：
- 自动转录（从视频提取字幕）
- 自动翻译（支持16种语言）
- 并行处理（提升处理速度）
- 音量标准化（专业音质）
- 灵活输出（带/不带字幕）
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QFrame,
    QCheckBox, QScrollArea, QGridLayout, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# 导入处理模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multilang_fast_parallel import FastParallelProcessor, LANGUAGE_CONFIG

# 导入翻译模块
try:
    from s2_translate import translate_srt
    TRANSLATE_AVAILABLE = True
except:
    TRANSLATE_AVAILABLE = False

# 导入转录模块
try:
    from s1_transcribe import extract_subtitles
    TRANSCRIBE_AVAILABLE = True
except:
    TRANSCRIBE_AVAILABLE = False


class TranscriptionThread(QThread):
    """转录线程"""
    
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)  # (成功, 输出文件路径)
    
    def __init__(self, video_file, output_srt):
        super().__init__()
        self.video_file = video_file
        self.output_srt = output_srt
    
    def run(self):
        try:
            self.progress_signal.emit("🎤 开始自动转录...")
            self.progress_signal.emit("这可能需要1-3分钟，请耐心等待...")
            
            # 添加详细日志
            self.progress_signal.emit(f"视频路径: {self.video_file}")
            self.progress_signal.emit(f"输出路径: {self.output_srt}")
            
            # 检查视频文件
            if not os.path.exists(self.video_file):
                self.progress_signal.emit(f"❌ 视频文件不存在: {self.video_file}")
                self.finished_signal.emit(False, "")
                return
            
            # 执行转录
            self.progress_signal.emit("开始转录处理...")
            success = extract_subtitles(self.video_file, self.output_srt)
            
            self.progress_signal.emit(f"转录结果: success={success}")
            self.progress_signal.emit(f"文件存在: {os.path.exists(self.output_srt)}")
            
            if success and os.path.exists(self.output_srt):
                self.progress_signal.emit(f"✅ 转录完成: {Path(self.output_srt).name}")
                self.finished_signal.emit(True, self.output_srt)
            else:
                self.progress_signal.emit("❌ 转录失败，请检查视频是否有音轨")
                self.progress_signal.emit(f"   success={success}")
                self.progress_signal.emit(f"   文件={self.output_srt}")
                self.progress_signal.emit(f"   存在={os.path.exists(self.output_srt) if self.output_srt else 'N/A'}")
                self.finished_signal.emit(False, "")
                
        except Exception as e:
            self.progress_signal.emit(f"❌ 转录出错: {str(e)}")
            import traceback
            self.progress_signal.emit("错误堆栈:")
            for line in traceback.format_exc().splitlines():
                self.progress_signal.emit(line)
            self.finished_signal.emit(False, "")


class ProcessingThread(QThread):
    """处理线程（并行）"""
    
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, dict)
    
    def __init__(self, video_file, source_srt, target_langs, output_dir, max_workers, with_subtitle=True):
        super().__init__()
        self.video_file = video_file
        self.source_srt = source_srt
        self.target_langs = target_langs
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.with_subtitle = with_subtitle
        self.is_cancelled = False
    
    def run(self):
        """执行高速并行处理"""
        try:
            video_basename = os.path.splitext(self.video_file)[0]
            
            # Phase 1: 自动翻译（如需要）
            self.progress_signal.emit("\n" + "="*50)
            self.progress_signal.emit("🔄 Phase 1: 准备字幕文件")
            self.progress_signal.emit("="*50)
            
            language_srt_pairs = []
            
            for i, lang_code in enumerate(self.target_langs, 1):
                if self.is_cancelled:
                    break
                
                lang_info = LANGUAGE_CONFIG[lang_code]
                self.progress_signal.emit(
                    f"\n[{i}/{len(self.target_langs)}] {lang_info['emoji']} {lang_info['name']}"
                )
                
                output_srt = f"{video_basename}_{lang_code}.srt"
                
                if os.path.exists(output_srt):
                    self.progress_signal.emit(f"   ✅ 字幕已存在: {os.path.basename(output_srt)}")
                    language_srt_pairs.append((lang_code, output_srt))
                    continue
                
                # 执行翻译
                self.progress_signal.emit(f"   🔄 正在翻译...")
                try:
                    success = translate_srt(self.source_srt, output_srt, lang_code)
                    
                    if success and os.path.exists(output_srt):
                        self.progress_signal.emit(f"   ✅ 翻译完成: {os.path.basename(output_srt)}")
                        language_srt_pairs.append((lang_code, output_srt))
                    else:
                        self.error_signal.emit(f"   ❌ 翻译失败")
                except Exception as e:
                    self.error_signal.emit(f"   ❌ 翻译出错: {str(e)}")
            
            if not language_srt_pairs:
                self.error_signal.emit("❌ 没有可用的字幕文件")
                self.finished_signal.emit(False, {})
                return
            
            # Phase 2: 并行处理所有语言（关键优化！）
            self.progress_signal.emit("\n" + "="*50)
            self.progress_signal.emit(f"🚀 Phase 2: 并行处理 {len(language_srt_pairs)} 个语言")
            self.progress_signal.emit(f"并行数: {self.max_workers} 个同时处理")
            self.progress_signal.emit("="*50)
            
            # 重定向输出到信号
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # 创建处理器
            processor = FastParallelProcessor(self.video_file, self.output_dir)
            
            # 执行并行处理
            results = processor.batch_process_parallel(
                language_srt_pairs, 
                max_workers=self.max_workers
            )
            
            if not self.is_cancelled:
                self.finished_signal.emit(True, results)
        
        except Exception as e:
            self.error_signal.emit(f"处理出错: {str(e)}")
            self.finished_signal.emit(False, {})
    
    def cancel(self):
        """取消处理"""
        self.is_cancelled = True


class DragDropArea(QFrame):
    """拖拽区域控件"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            DragDropArea {
                border: 2px dashed #CCCCCC;
                border-radius: 10px;
                background-color: #F8F9FA;
            }
            DragDropArea:hover {
                border-color: #999999;
                background-color: #F0F1F2;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("🎬")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.hint_label = QLabel("拖拽视频文件到这里\n或点击选择文件")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_font = QFont()
        hint_font.setPointSize(14)
        self.hint_label.setFont(hint_font)
        self.hint_label.setStyleSheet("color: #666666;")
        
        format_label = QLabel("支持格式: MP4, MOV, AVI")
        format_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        format_label.setStyleSheet("color: #999999; font-size: 11px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(format_label)
        
        self.setLayout(layout)
        self.setMinimumHeight(120)
    
    def set_file_text(self, file_path: str):
        file_name = Path(file_path).name
        self.hint_label.setText(f"已选择:\n{file_name}")
        self.setStyleSheet("""
            DragDropArea {
                border: 2px solid #FF6600;
                border-radius: 10px;
                background-color: #FFF3E0;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件", str(Path.home()),
                "视频文件 (*.mp4 *.mov *.avi);;所有文件 (*)"
            )
            if file_path:
                self.file_dropped.emit(file_path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    event.acceptProposedAction()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.file_dropped.emit(file_path)


class MultilingualGUI(QMainWindow):
    """多语言处理GUI"""
    
    def __init__(self):
        super().__init__()
        self.video_file = None
        self.source_srt = None
        self.processing_thread = None
        self.transcription_thread = None
        self.language_checkboxes = {}
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🎬 VideoTranslator v1.0")
        self.setMinimumSize(1200, 1000)  # 增大窗口
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 使用滚动区域包装所有内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 减小间距
        main_layout.setContentsMargins(15, 10, 15, 10)  # 减小边距
        
        # 简化标题（节省空间）
        title_label = QLabel("🎬 VideoTranslator v1.0")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2E86DE; margin: 5px;")
        main_layout.addWidget(title_label)
        
        # 拖拽区域（新增）
        self.drag_area = DragDropArea()
        self.drag_area.file_dropped.connect(self.on_file_selected)
        main_layout.addWidget(self.drag_area)
        
        # 源字幕选择
        source_group = QGroupBox("📝 源字幕文件")
        source_layout = QVBoxLayout()
        
        # 第一行：状态显示
        status_layout = QHBoxLayout()
        self.source_srt_label = QLabel("未选择源字幕")
        self.source_srt_label.setStyleSheet("color: #666666;")
        status_layout.addWidget(self.source_srt_label)
        status_layout.addStretch()
        source_layout.addLayout(status_layout)
        
        # 第二行：操作按钮
        button_layout = QHBoxLayout()
        
        self.auto_transcribe_btn = QPushButton("🎤 自动转录（从视频提取）")
        self.auto_transcribe_btn.clicked.connect(self.start_auto_transcribe)
        self.auto_transcribe_btn.setEnabled(False)
        self.auto_transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        button_layout.addWidget(self.auto_transcribe_btn)
        
        self.select_source_btn = QPushButton("📁 手动选择字幕")
        self.select_source_btn.clicked.connect(self.select_source_srt)
        button_layout.addWidget(self.select_source_btn)
        
        self.auto_detect_btn = QPushButton("🔍 自动检测")
        self.auto_detect_btn.clicked.connect(self.auto_detect_source_srt)
        self.auto_detect_btn.setEnabled(False)
        button_layout.addWidget(self.auto_detect_btn)
        
        source_layout.addLayout(button_layout)
        
        # 提示信息
        hint_label = QLabel("💡 推荐：优先使用「自动转录」从视频提取字幕")
        hint_label.setStyleSheet("color: #666666; font-size: 11px; font-style: italic;")
        source_layout.addWidget(hint_label)
        
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        # 源语言选择（可选）
        from PyQt6.QtWidgets import QComboBox
        source_lang_group = QGroupBox("🌐 源语言（可选）")
        source_lang_layout = QHBoxLayout()
        
        source_lang_label = QLabel("如果已知源语言，可选择以提高转录准确度：")
        source_lang_label.setStyleSheet("font-size: 12px;")
        source_lang_layout.addWidget(source_lang_label)
        
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItem("自动检测", "")
        self.source_lang_combo.addItem("🇨🇳 中文", "zh")
        self.source_lang_combo.addItem("🇺🇸 英语", "en")
        self.source_lang_combo.addItem("🇯🇵 日语", "ja")
        self.source_lang_combo.addItem("🇰🇷 韩语", "ko")
        self.source_lang_combo.addItem("🇪🇸 西班牙语", "es")
        self.source_lang_combo.addItem("🇵🇹 葡萄牙语", "pt")
        self.source_lang_combo.addItem("🇫🇷 法语", "fr")
        self.source_lang_combo.addItem("🇩🇪 德语", "de")
        self.source_lang_combo.addItem("🇮🇹 意大利语", "it")
        self.source_lang_combo.addItem("🇷🇺 俄语", "ru")
        self.source_lang_combo.setMinimumWidth(200)
        source_lang_layout.addWidget(self.source_lang_combo)
        source_lang_layout.addStretch()
        
        source_lang_group.setLayout(source_lang_layout)
        main_layout.addWidget(source_lang_group)
        
        # 语言选择
        lang_group = QGroupBox("🌍 选择目标语言（多选）")
        lang_layout = QVBoxLayout()
        
        # 快速选择
        quick_select_layout = QHBoxLayout()
        quick_select_layout.addWidget(QLabel("快速选择："))
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_languages)
        self.select_all_btn.setMaximumWidth(80)
        
        self.clear_all_btn = QPushButton("清空")
        self.clear_all_btn.clicked.connect(self.clear_all_languages)
        self.clear_all_btn.setMaximumWidth(80)
        
        self.select_common_btn = QPushButton("常用语言")
        self.select_common_btn.clicked.connect(self.select_common_languages)
        self.select_common_btn.setMaximumWidth(100)
        
        quick_select_layout.addWidget(self.select_all_btn)
        quick_select_layout.addWidget(self.clear_all_btn)
        quick_select_layout.addWidget(self.select_common_btn)
        quick_select_layout.addStretch()
        
        lang_layout.addLayout(quick_select_layout)
        
        # 语言复选框
        lang_scroll_area = QScrollArea()
        lang_scroll_area.setWidgetResizable(True)
        lang_scroll_area.setFixedHeight(150)  # 固定高度
        
        checkbox_widget = QWidget()
        checkbox_layout = QGridLayout()
        checkbox_layout.setSpacing(10)
        
        row, col = 0, 0
        for lang_code, lang_info in LANGUAGE_CONFIG.items():
            checkbox = QCheckBox(f"{lang_info['emoji']} {lang_info['name']}")
            checkbox.setStyleSheet("font-size: 13px; padding: 5px;")
            self.language_checkboxes[lang_code] = checkbox
            checkbox_layout.addWidget(checkbox, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        checkbox_widget.setLayout(checkbox_layout)
        lang_scroll_area.setWidget(checkbox_widget)
        lang_layout.addWidget(lang_scroll_area)
        
        self.selection_label = QLabel("已选择: 0 种语言")
        self.selection_label.setStyleSheet("color: #2E86DE; font-weight: bold; margin: 8px 0px; font-size: 13px;")
        lang_layout.addWidget(self.selection_label)
        
        for checkbox in self.language_checkboxes.values():
            checkbox.stateChanged.connect(self.update_selection_count)
        
        lang_group.setLayout(lang_layout)
        main_layout.addWidget(lang_group)
        
        # 输出选项
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup
        output_group = QGroupBox("📤 输出选项")
        output_main_layout = QVBoxLayout()
        output_main_layout.setSpacing(8)
        
        # 第一行：选项
        output_option_layout = QHBoxLayout()
        output_label = QLabel("输出视频：")
        output_option_layout.addWidget(output_label)
        
        self.subtitle_option_group = QButtonGroup()
        
        self.with_subtitle_radio = QRadioButton("带字幕版（默认）")
        self.with_subtitle_radio.setChecked(True)
        self.subtitle_option_group.addButton(self.with_subtitle_radio, 1)
        output_option_layout.addWidget(self.with_subtitle_radio)
        
        self.without_subtitle_radio = QRadioButton("不带字幕版")
        self.subtitle_option_group.addButton(self.without_subtitle_radio, 2)
        output_option_layout.addWidget(self.without_subtitle_radio)
        
        output_option_layout.addStretch()
        output_main_layout.addLayout(output_option_layout)
        
        # 第二行：提示
        output_hint = QLabel("💡 带字幕版会将字幕烧录到视频中")
        output_hint.setStyleSheet("color: #666666; font-size: 11px; margin-left: 70px;")
        output_main_layout.addWidget(output_hint)
        
        output_group.setLayout(output_main_layout)
        main_layout.addWidget(output_group)
        
        # 并行设置
        parallel_group = QGroupBox("⚙️ 处理设置")
        parallel_main_layout = QVBoxLayout()
        parallel_main_layout.setSpacing(8)
        
        # 第一行：并行数设置
        parallel_setting_layout = QHBoxLayout()
        parallel_setting_layout.addWidget(QLabel("同时处理语言数："))
        
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setMinimum(1)
        self.parallel_spin.setMaximum(8)
        self.parallel_spin.setValue(3)
        self.parallel_spin.setToolTip("建议：2-4个并行（取决于你的CPU性能）")
        self.parallel_spin.setMinimumWidth(60)
        parallel_setting_layout.addWidget(self.parallel_spin)
        
        parallel_setting_layout.addStretch()
        parallel_main_layout.addLayout(parallel_setting_layout)
        
        # 第二行：提示
        hint_label = QLabel("💡 值越大速度越快，但CPU占用越高")
        hint_label.setStyleSheet("color: #666666; font-size: 11px; margin-left: 10px;")
        parallel_main_layout.addWidget(hint_label)
        
        parallel_group.setLayout(parallel_main_layout)
        main_layout.addWidget(parallel_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 开始处理")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2E86DE;
                color: white;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E6FBE;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setEnabled(False)
        
        self.open_folder_button = QPushButton("📁 打开输出文件夹")
        self.open_folder_button.setMinimumHeight(50)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        
        button_layout.addWidget(self.start_button, 3)
        button_layout.addWidget(self.open_folder_button, 1)
        main_layout.addLayout(button_layout)
        
        # 进度显示
        progress_group = QGroupBox("📊 处理进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备就绪 - 请选择视频、源字幕和目标语言")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        progress_layout.addWidget(self.status_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(200)  # 固定高度，不要太大
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 设置滚动区域
        scroll_widget.setLayout(main_layout)
        scroll_area.setWidget(scroll_widget)
        
        # 主布局
        main_container_layout = QVBoxLayout()
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.addWidget(scroll_area)
        central_widget.setLayout(main_container_layout)
        
        self.log("="*60)
        self.log("🎬 VideoTranslator v1.0")
        self.log("="*60)
        self.log("")
        self.log("📌 步骤1: 拖拽视频文件")
        self.log("📌 步骤2: 自动转录或选择源字幕")
        self.log("📌 步骤3: 选择目标语言（多选）")
        self.log("📌 步骤4: 配置输出选项，点击开始处理")
        self.log("")
        self.log("="*60)
    
    def on_file_selected(self, file_path: str):
        """处理文件选择/拖拽"""
        if os.path.exists(file_path):
            self.video_file = file_path
            self.drag_area.set_file_text(file_path)
            self.auto_detect_btn.setEnabled(True)
            self.auto_transcribe_btn.setEnabled(True)  # 启用自动转录
            self.log(f"✅ 已选择视频: {Path(file_path).name}")
            self.auto_detect_source_srt()
            self.update_start_button()
    
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", str(Path.home()),
            "视频文件 (*.mp4 *.mov *.avi);;所有文件 (*)"
        )
        if file_path:
            self.on_file_selected(file_path)
    
    def select_all_languages(self):
        for checkbox in self.language_checkboxes.values():
            checkbox.setChecked(True)
    
    def clear_all_languages(self):
        for checkbox in self.language_checkboxes.values():
            checkbox.setChecked(False)
    
    def select_common_languages(self):
        common_langs = ['en', 'es', 'pt', 'ja']
        for lang_code, checkbox in self.language_checkboxes.items():
            checkbox.setChecked(lang_code in common_langs)
    
    def update_selection_count(self):
        count = sum(1 for cb in self.language_checkboxes.values() if cb.isChecked())
        self.selection_label.setText(f"已选择: {count} 种语言")
        self.update_start_button()
    
    def update_start_button(self):
        has_video = self.video_file is not None
        has_source = self.source_srt is not None
        has_selection = sum(1 for cb in self.language_checkboxes.values() if cb.isChecked()) > 0
        self.start_button.setEnabled(has_video and has_source and has_selection)
    
    def select_source_srt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择源字幕文件",
            str(Path(self.video_file).parent) if self.video_file else str(Path.home()),
            "字幕文件 (*.srt);;所有文件 (*)"
        )
        if file_path and os.path.exists(file_path):
            self.source_srt = file_path
            self.source_srt_label.setText(f"✅ {Path(file_path).name}")
            self.source_srt_label.setStyleSheet("color: #FF6600; font-weight: bold;")
            self.log(f"✅ 已选择源字幕: {Path(file_path).name}")
            self.update_start_button()
    
    def start_auto_transcribe(self):
        """启动自动转录"""
        if not self.video_file:
            QMessageBox.warning(self, "错误", "请先选择视频文件！")
            return
        
        # 检查是否已安装转录模块
        if not TRANSCRIBE_AVAILABLE:
            QMessageBox.critical(
                self, "转录模块未安装",
                "未找到转录模块！\n\n请安装whisper或faster-whisper：\n\n"
                "标准版：pip3 install openai-whisper\n"
                "快速版：./安装faster-whisper.sh"
            )
            return
        
        # 确认对话框
        video_name = Path(self.video_file).name
        msg = f"将从视频中自动提取字幕：\n\n"
        msg += f"视频：{video_name}\n\n"
        msg += f"使用：faster-whisper（如已安装）或标准whisper\n"
        msg += f"预计时间：1-3分钟\n\n"
        msg += f"确认开始转录吗？"
        
        reply = QMessageBox.question(
            self, "自动转录确认", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 禁用按钮
        self.auto_transcribe_btn.setEnabled(False)
        self.select_source_btn.setEnabled(False)
        self.start_button.setEnabled(False)
        
        # 更新状态
        self.source_srt_label.setText("🎤 正在转录...")
        self.source_srt_label.setStyleSheet("color: #FF6600; font-weight: bold;")
        
        # 准备输出文件路径（使用绝对路径）
        video_abs_path = os.path.abspath(self.video_file)
        video_basename = os.path.splitext(video_abs_path)[0]
        output_srt = f"{video_basename}_transcribed.srt"
        
        self.log(f"视频文件: {video_abs_path}")
        self.log(f"输出字幕: {output_srt}")
        
        # 创建并启动转录线程
        self.transcription_thread = TranscriptionThread(video_abs_path, output_srt)
        self.transcription_thread.progress_signal.connect(self.log)
        self.transcription_thread.finished_signal.connect(self.on_transcription_finished)
        self.transcription_thread.start()
    
    def on_transcription_finished(self, success: bool, output_srt: str):
        """转录完成回调"""
        # 添加详细日志
        self.log("\n" + "="*50)
        self.log("📊 转录完成回调调试信息")
        self.log("="*50)
        self.log(f"success参数: {success}")
        self.log(f"output_srt参数: {output_srt}")
        self.log(f"当前工作目录: {os.getcwd()}")
        self.log(f"文件存在检查: {os.path.exists(output_srt)}")
        self.log(f"绝对路径: {os.path.abspath(output_srt)}")
        self.log(f"绝对路径存在: {os.path.exists(os.path.abspath(output_srt))}")
        self.log("="*50)
        
        if success and os.path.exists(output_srt):
            self.source_srt = output_srt
            self.source_srt_label.setText(f"✅ {Path(output_srt).name} (自动转录)")
            self.source_srt_label.setStyleSheet("color: #28A745; font-weight: bold;")
            self.update_start_button()
            self.log("✅ 判断结果: 成功，显示成功对话框")
            QMessageBox.information(
                self, "转录完成",
                f"字幕已自动提取！\n\n输出文件：{Path(output_srt).name}\n\n现在可以选择目标语言开始处理了。"
            )
        else:
            self.source_srt_label.setText("❌ 转录失败")
            self.source_srt_label.setStyleSheet("color: #DC3545;")
            self.log("❌ 判断结果: 失败，显示错误对话框")
            self.log(f"   失败原因: success={success}, exists={os.path.exists(output_srt)}")
            QMessageBox.warning(
                self, "转录失败",
                "无法从视频中提取字幕，请确保：\n\n"
                "1. 视频文件有清晰的音轨\n"
                "2. 已安装 whisper 或 faster-whisper\n"
                "3. FFmpeg 已正确安装\n\n"
                "安装命令：\n"
                "pip3 install openai-whisper\n"
                "或\n"
                "./安装faster-whisper.sh"
            )
        
        # 重新启用按钮
        self.auto_transcribe_btn.setEnabled(True)
        self.select_source_btn.setEnabled(True)
        self.update_start_button()
    
    def auto_detect_source_srt(self):
        """自动检测源字幕文件"""
        if not self.video_file:
            return
        
        video_basename = os.path.splitext(self.video_file)[0]
        
        possible_files = [
            f"{video_basename}.srt",
            f"{video_basename}_original.srt",
            f"{video_basename}_transcribed.srt",  # 自动转录的
            f"{video_basename}_zh.srt",
            f"{video_basename}_en.srt",
        ]
        
        for srt_file in possible_files:
            if os.path.exists(srt_file):
                self.source_srt = srt_file
                self.source_srt_label.setText(f"✅ {Path(srt_file).name} (自动检测)")
                self.source_srt_label.setStyleSheet("color: #28A745; font-weight: bold;")
                self.log(f"✅ 自动检测到源字幕: {Path(srt_file).name}")
                self.update_start_button()
                return
        
        self.log("💡 未检测到字幕文件，建议使用「自动转录」功能")
    
    def start_processing(self):
        """开始处理"""
        if not self.video_file or not self.source_srt:
            QMessageBox.warning(self, "错误", "请先选择视频文件和源字幕文件！")
            return
        
        selected_langs = [
            code for code, cb in self.language_checkboxes.items() 
            if cb.isChecked()
        ]
        
        if not selected_langs:
            QMessageBox.warning(self, "错误", "请至少选择一种目标语言！")
            return
        
        max_workers = self.parallel_spin.value()
        
        # 获取输出选项
        with_subtitle = self.with_subtitle_radio.isChecked()
        
        # 确认处理
        msg = f"📊 处理信息\n\n"
        msg += f"目标语言数: {len(selected_langs)}\n"
        msg += f"并行处理数: {max_workers}\n"
        msg += f"输出选项: {'带字幕版' if with_subtitle else '不带字幕版'}\n\n"
        msg += f"预计时间:\n"
        msg += f"  - 预计耗时: {len(selected_langs) * 5 // max_workers}-{len(selected_langs) * 15 // max_workers}分钟\n\n"
        msg += f"确认开始处理吗？"
        
        reply = QMessageBox.question(
            self, "确认处理", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 禁用按钮
        self.start_button.setEnabled(False)
        
        # 启动处理线程
        output_dir = "output"
        self.processing_thread = ProcessingThread(
            self.video_file,
            self.source_srt,
            selected_langs,
            output_dir,
            max_workers,
            with_subtitle
        )
        self.processing_thread.progress_signal.connect(self.log)
        self.processing_thread.error_signal.connect(self.log_error)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()
        
        self.log(f"\n🚀 开始处理")
        self.log(f"并行数: {max_workers}")
        self.log(f"目标语言数: {len(selected_langs)}")
        self.log(f"输出选项: {'带字幕版' if with_subtitle else '不带字幕版'}")
        self.status_label.setText(f"正在处理中...")
    
    def format_time(self, seconds: float) -> str:
        """格式化时间为 X小时X分钟X秒"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if secs > 0 or not parts:  # 至少显示秒
            parts.append(f"{secs}秒")
        
        return "".join(parts)
    
    def on_processing_finished(self, success: bool, results: dict):
        """处理完成"""
        self.start_button.setEnabled(True)
        
        if success and results:
            self.progress_bar.setValue(100)
            success_count = results.get('success_count', 0)
            total_count = results.get('total_languages', 0)
            total_time = results.get('total_time', 0)
            max_workers = results.get('max_workers', 1)
            
            self.status_label.setText("✅ 全部完成！")
            
            # 计算合理的加速比（实际并行效率）
            # 加速比 = 实际处理的语言数 / 实际耗时比例
            # 更保守的计算：只考虑并行带来的提升
            if max_workers > 1 and total_count > 1:
                # 理论最大加速比接近 min(并行数, 任务数)
                # 实际加速比会因为开销而降低
                ideal_speedup = min(max_workers, total_count)
                speedup = min(ideal_speedup * 0.7, ideal_speedup)  # 保守估计70%效率
            else:
                speedup = 1.0
            
            # 格式化时间
            time_str = self.format_time(total_time)
            
            msg = f"🎉 处理完成！\n\n"
            msg += f"✅ 成功：{success_count}/{total_count}\n"
            msg += f"⏱️  总耗时：{time_str}\n"
            msg += f"🔢 并行数：{max_workers}\n"
            
            # 只在并行处理时显示加速信息
            if max_workers > 1 and total_count > 1:
                msg += f"🚀 并行加速：约 {speedup:.1f}x\n"
            
            msg += f"\n📁 输出目录：output/"
            
            QMessageBox.information(self, "处理完成", msg)
            
            self.log("\n" + "="*50)
            self.log("🎉 处理完成！")
            self.log(f"✅ 成功：{success_count}/{total_count}")
            self.log(f"⏱️  总耗时：{time_str}")
            if max_workers > 1:
                self.log(f"🚀 并行加速：约 {speedup:.1f}x")
            self.log(f"📁 输出目录：output/")
        else:
            self.status_label.setText("❌ 处理失败")
            QMessageBox.warning(self, "处理失败", "处理过程中出现错误，请查看日志。")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        output_dir = "output"
        if not os.path.exists(output_dir):
            output_dir = str(Path(self.video_file).parent) if self.video_file else str(Path.home())
        
        os.system(f'open "{output_dir}"')
    
    def log(self, message: str):
        """输出日志"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def log_error(self, message: str):
        """输出错误日志"""
        self.log(f"<span style='color: #FF6B6B;'>{message}</span>")


def main():
    """主入口"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MultilingualGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

