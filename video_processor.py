#!/usr/bin/env python3
"""
视频处理业务逻辑封装
提供非交互式的API接口供GUI调用
"""

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, List


class VideoProcessor:
    """视频处理器 - 封装所有视频处理脚本的调用"""
    
    def __init__(self):
        self.current_process = None
        self.is_cancelled = False
        
        # 脚本映射
        self.scripts = {
            'transcribe': 's1_transcribe.py',
            'translate': 's2_translate.py',
            'voiceover': 's3_generate_voiceover.py',
            'merge': 's5_burn_subtitles_simple.py',
            'remove_subtitle': 's6_remove_subtitle.py',
            'clean_metadata': 's7_clean_metadata.py'
        }
        
        # 语言代码映射
        self.language_codes = {
            '中文': 'zh',
            '英语': 'en',
            '日语': 'ja',
            '韩语': 'ko',
            '法语': 'fr',
            '德语': 'de',
            '西语': 'es',
            '葡语': 'pt',
            '俄语': 'ru',
            '阿拉伯语': 'ar',
            '印度语': 'hi',
            '泰语': 'th',
            '越南语': 'vi',
            '意大利语': 'it',
            '土耳其语': 'tr',
            '印尼语': 'id'
        }
        
        # 默认音色映射（按语言自动选择）
        self.default_voices = {
            'zh': 'zh-CN-XiaoxiaoNeural',   # 中文女声
            'en': 'en-US-JennyNeural',      # 英语女声
            'ja': 'ja-JP-NanamiNeural',     # 日语女声
            'ko': 'ko-KR-SunHiNeural',      # 韩语女声
            'fr': 'fr-FR-DeniseNeural',     # 法语女声
            'de': 'de-DE-KatjaNeural',      # 德语女声
            'es': 'es-ES-ElviraNeural',     # 西语女声
            'pt': 'pt-BR-FranciscaNeural',  # 葡语女声（巴西）
            'ru': 'ru-RU-DariyaNeural',     # 俄语女声
            'ar': 'ar-SA-ZariyahNeural',    # 阿拉伯语女声
            'hi': 'hi-IN-SwaraNeural',      # 印度语女声
            'th': 'th-TH-PremwadeeNeural',  # 泰语女声
            'vi': 'vi-VN-HoaiMyNeural',     # 越南语女声
            'it': 'it-IT-ElsaNeural',       # 意大利语女声
            'tr': 'tr-TR-EmelNeural',       # 土耳其语女声
            'id': 'id-ID-GadisNeural',      # 印尼语女声
        }
    
    def cancel(self):
        """取消当前操作"""
        self.is_cancelled = True
        if self.current_process:
            try:
                self.current_process.terminate()
            except:
                pass
    
    def run_script(
        self, 
        script_name: str, 
        args: List[str],
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        运行指定脚本
        
        Args:
            script_name: 脚本名称
            args: 参数列表
            progress_callback: 进度回调函数
            error_callback: 错误回调函数
            
        Returns:
            bool: 是否成功
        """
        if self.is_cancelled:
            return False
        
        try:
            cmd = ['python3', script_name] + args
            
            if progress_callback:
                progress_callback(f"🔄 执行命令: {' '.join(cmd)}")
            
            # 使用 Popen 以便实时获取输出
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 实时读取输出
            for line in self.current_process.stdout:
                if self.is_cancelled:
                    self.current_process.terminate()
                    return False
                
                line = line.strip()
                if line and progress_callback:
                    progress_callback(line)
            
            self.current_process.wait()
            
            if self.current_process.returncode == 0:
                if progress_callback:
                    progress_callback("✅ 执行成功！")
                return True
            else:
                if error_callback:
                    error_callback(f"❌ 执行失败，退出码: {self.current_process.returncode}")
                return False
                
        except FileNotFoundError:
            if error_callback:
                error_callback(f"❌ 脚本文件不存在: {script_name}")
            return False
        except Exception as e:
            if error_callback:
                error_callback(f"❌ 执行出错: {str(e)}")
            return False
        finally:
            self.current_process = None
    
    def transcribe(
        self,
        video_file: str,
        output_file: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """提取字幕（语音识别）"""
        if progress_callback:
            progress_callback("📝 步骤1: 提取字幕（语音识别）...")
        
        return self.run_script(
            self.scripts['transcribe'],
            [video_file, output_file],
            progress_callback,
            error_callback
        )
    
    def translate(
        self,
        input_srt: str,
        output_srt: str,
        target_lang: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """翻译字幕"""
        if progress_callback:
            progress_callback(f"🌍 步骤2: 翻译字幕到 {target_lang}...")
        
        return self.run_script(
            self.scripts['translate'],
            [input_srt, output_srt, target_lang],
            progress_callback,
            error_callback
        )
    
    def generate_voiceover(
        self,
        input_srt: str,
        output_audio: str,
        target_lang: str,
        voice_code: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """生成配音"""
        if progress_callback:
            progress_callback("🎙️ 步骤3: 生成配音...")
        
        # 如果没有指定音色，使用默认音色
        if not voice_code:
            voice_code = self.default_voices.get(target_lang, 'en-US-JennyNeural')
            if progress_callback:
                progress_callback(f"使用默认音色: {voice_code}")
        
        args = [input_srt, output_audio, voice_code]
        
        return self.run_script(
            self.scripts['voiceover'],
            args,
            progress_callback,
            error_callback
        )
    
    def merge_video(
        self,
        video_file: str,
        subtitle_file: str,
        output_video: str,
        audio_file: str,
        position: str = 'bottom',
        margin: int = 10,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """合成最终视频"""
        if progress_callback:
            progress_callback("🎬 步骤4: 合成最终视频...")
        
        position_arg = f'--{position}'
        margin_arg = f'--margin={margin}'
        
        return self.run_script(
            self.scripts['merge'],
            [video_file, subtitle_file, output_video, audio_file, position_arg, margin_arg],
            progress_callback,
            error_callback
        )
    
    def full_workflow(
        self,
        video_file: str,
        target_lang: str,
        voice_code: Optional[str] = None,
        subtitle_position: str = 'bottom',
        margin: int = 10,
        progress_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        step_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, str]:
        """
        完整工作流
        
        Returns:
            Dict[str, str]: 生成的文件路径字典
        """
        self.is_cancelled = False
        video_stem = Path(video_file).stem
        
        # 生成文件名
        original_srt = f"{video_stem}_original.srt"
        translated_srt = f"{video_stem}_{target_lang}.srt"
        voiceover_audio = f"{video_stem}_{target_lang}_voiceover.mp3"
        final_video = f"{video_stem}_{target_lang}_final.mp4"
        
        result = {
            'original_srt': original_srt,
            'translated_srt': translated_srt,
            'voiceover_audio': voiceover_audio,
            'final_video': final_video,
            'success': False
        }
        
        try:
            # 步骤1: 提取字幕
            if step_callback:
                step_callback(1, 4)
            if progress_callback:
                progress_callback("\n" + "="*60 + "\n步骤 1/4: 提取原语言字幕\n" + "="*60)
            
            if not self.transcribe(video_file, original_srt, progress_callback, error_callback):
                if error_callback:
                    error_callback("❌ 步骤1失败，工作流终止")
                return result
            
            # 步骤2: 翻译
            if step_callback:
                step_callback(2, 4)
            if progress_callback:
                progress_callback("\n" + "="*60 + f"\n步骤 2/4: 翻译成 {target_lang}\n" + "="*60)
            
            if not self.translate(original_srt, translated_srt, target_lang, progress_callback, error_callback):
                if error_callback:
                    error_callback("❌ 步骤2失败，工作流终止")
                return result
            
            # 步骤3: 生成配音
            if step_callback:
                step_callback(3, 4)
            if progress_callback:
                progress_callback("\n" + "="*60 + "\n步骤 3/4: 生成配音\n" + "="*60)
            
            if not self.generate_voiceover(translated_srt, voiceover_audio, target_lang, voice_code, progress_callback, error_callback):
                if error_callback:
                    error_callback("❌ 步骤3失败，工作流终止")
                return result
            
            # 步骤4: 合成视频
            if step_callback:
                step_callback(4, 4)
            if progress_callback:
                progress_callback("\n" + "="*60 + "\n步骤 4/4: 合成最终视频\n" + "="*60)
            
            if not self.merge_video(
                video_file, translated_srt, final_video, voiceover_audio,
                subtitle_position, margin, progress_callback, error_callback
            ):
                if error_callback:
                    error_callback("❌ 步骤4失败，工作流终止")
                return result
            
            result['success'] = True
            if progress_callback:
                progress_callback("\n" + "="*60 + "\n🎉 完整工作流执行成功！\n" + "="*60)
            
        except Exception as e:
            if error_callback:
                error_callback(f"❌ 工作流出错: {str(e)}")
        
        return result
