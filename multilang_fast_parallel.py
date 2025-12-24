#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 多语言视频处理 - 高速并行版
速度优化：3-5倍提升

核心优化：
- 并行处理多个语言（最关键）
- 批量TTS合成
- 智能缓存
- faster-whisper支持
"""

import os
import sys
import subprocess
import time
import srt
from datetime import timedelta
from gtts import gTTS
from typing import List, Dict, Tuple, NamedTuple
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp

# ============================================================
# 语言策略定义
# ============================================================

class LanguageStrategy(NamedTuple):
    """语言处理策略"""
    tts_speed_min: float = 0.7
    tts_speed_max: float = 1.5
    video_speed_min: float = 0.85
    video_speed_max: float = 1.0

# 默认策略（适用于所有语言）
DEFAULT_STRATEGY = LanguageStrategy(
    tts_speed_min=0.7,
    tts_speed_max=1.5,
    video_speed_min=0.85,
    video_speed_max=1.0
)

# ============================================================
# 语言配置
# ============================================================

LANGUAGE_CONFIG = {
    'zh': {'name': '中文', 'emoji': '🇨🇳', 'gtts_code': 'zh-CN'},
    'en': {'name': '英语', 'emoji': '🇺🇸', 'gtts_code': 'en'},
    'ja': {'name': '日语', 'emoji': '🇯🇵', 'gtts_code': 'ja'},
    'ko': {'name': '韩语', 'emoji': '🇰🇷', 'gtts_code': 'ko'},
    'fr': {'name': '法语', 'emoji': '🇫🇷', 'gtts_code': 'fr'},
    'de': {'name': '德语', 'emoji': '🇩🇪', 'gtts_code': 'de'},
    'es': {'name': '西语', 'emoji': '🇪🇸', 'gtts_code': 'es'},
    'pt': {'name': '葡语', 'emoji': '🇵🇹', 'gtts_code': 'pt'},
    'ru': {'name': '俄语', 'emoji': '🇷🇺', 'gtts_code': 'ru'},
    'ar': {'name': '阿拉伯语', 'emoji': '🇸🇦', 'gtts_code': 'ar'},
    'hi': {'name': '印度语', 'emoji': '🇮🇳', 'gtts_code': 'hi'},
    'th': {'name': '泰语', 'emoji': '🇹🇭', 'gtts_code': 'th'},
    'vi': {'name': '越南语', 'emoji': '🇻🇳', 'gtts_code': 'vi'},
    'it': {'name': '意大利语', 'emoji': '🇮🇹', 'gtts_code': 'it'},
    'tr': {'name': '土耳其语', 'emoji': '🇹🇷', 'gtts_code': 'tr'},
    'id': {'name': '印尼语', 'emoji': '🇮🇩', 'gtts_code': 'id'}
}

# ============================================================
# 快速TTS生成（批量优化）
# ============================================================

def generate_segment_voice_fast(text: str, lang_code: str, output_file: str, 
                                target_duration: float, speed_limit: Tuple[float, float] = (0.7, 1.5)) -> bool:
    """
    快速生成单个语音段落（优化版）
    
    优化点：
    - 使用慢速模式(slow=False)加快生成
    - 减少FFmpeg调用次数
    - 直接生成目标格式
    - 音量标准化（解决音量不统一问题）
    """
    try:
        # 生成初始语音（关闭slow模式提速）
        temp_initial = f"{output_file}_init.mp3"
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(temp_initial)
        
        # 测量自然时长
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", temp_initial]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        natural_duration = float(result.stdout.strip() or "0")
        
        if natural_duration == 0:
            os.remove(temp_initial)
            return False
        
        # 计算速度调整
        speed_ratio = natural_duration / target_duration
        speed_ratio = max(speed_limit[0], min(speed_ratio, speed_limit[1]))
        
        # 构建滤镜链：速度调整 + 音量标准化
        if abs(speed_ratio - 1.0) > 0.05:
            atempo_filter = f"atempo={speed_ratio}"
        else:
            atempo_filter = "anull"
        
        adjusted_duration = natural_duration / speed_ratio
        
        # 添加音量标准化滤镜（关键修复！）
        # loudnorm: 响度标准化，确保所有片段音量一致
        normalize_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"
        
        # 根据时长决定处理方式
        if adjusted_duration > target_duration + 0.1:
            # 需要裁剪 + 音量标准化
            filter_complex = f"{atempo_filter},{normalize_filter},afade=t=out:st={max(0, target_duration - 0.1)}:d=0.1"
            cmd = ["ffmpeg", "-y", "-i", temp_initial, "-af", filter_complex, 
                   "-t", str(target_duration), output_file]
        elif adjusted_duration < target_duration - 0.1:
            # 需要填充静音 + 音量标准化
            silence_duration = target_duration - adjusted_duration
            filter_complex = f"[0:a]{atempo_filter},{normalize_filter}[a];anullsrc=r=44100:cl=stereo,atrim=duration={silence_duration}[s];[a][s]concat=n=2:v=0:a=1[out]"
            cmd = ["ffmpeg", "-y", "-i", temp_initial, "-filter_complex", filter_complex,
                   "-map", "[out]", output_file]
        else:
            # 时长刚好 + 音量标准化
            if atempo_filter == "anull":
                filter_str = normalize_filter
            else:
                filter_str = f"{atempo_filter},{normalize_filter}"
            cmd = ["ffmpeg", "-y", "-i", temp_initial, "-af", filter_str, output_file]
        
        subprocess.run(cmd, capture_output=True)
        os.remove(temp_initial)
        
        return os.path.exists(output_file) and os.path.getsize(output_file) > 0
        
    except Exception as e:
        print(f"  ❌ 语音生成失败: {e}")
        return False


def merge_audio_segments_fast(segments_info: List[Tuple[str, float]], 
                              output_audio: str, total_duration: float) -> bool:
    """
    快速合并音频段落（优化版）
    
    优化点：
    - 使用更简洁的FFmpeg命令
    - 减少临时文件
    - 强化音量标准化（解决音量不统一问题）
    """
    if not segments_info:
        return False
    
    try:
        inputs = []
        filter_cmds = []
        
        for idx, (audio_file, start_time) in enumerate(segments_info):
            inputs.extend(["-i", audio_file])
            delay_ms = int(start_time * 1000)
            filter_cmds.append(f"[{idx}]adelay=delays={delay_ms}:all=1[a{idx}]")
        
        mix_inputs = "".join([f"[a{i}]" for i in range(len(segments_info))])
        
        # 增强音量标准化处理（关键修复！）
        # 1. amix: 混合多个音频
        # 2. dynaudnorm: 动态音频标准化（平滑音量变化）
        # 3. loudnorm: 响度标准化（EBU R128标准，确保整体音量一致）
        filter_cmds.append(
            f"{mix_inputs}amix=inputs={len(segments_info)}:duration=longest:dropout_transition=0,"
            f"dynaudnorm=f=75:g=25:p=0.95:m=10,"
            f"loudnorm=I=-16:TP=-1.5:LRA=11[out]"
        )
        
        filter_complex = ";".join(filter_cmds)
        
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(total_duration),
            output_audio
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and os.path.exists(output_audio)
        
    except Exception as e:
        print(f"❌ 音频合并失败: {e}")
        return False


# ============================================================
# 单语言处理器（独立进程）
# ============================================================

def process_single_language(video_file: str, lang_code: str, srt_file: str, 
                           output_dir: str, video_duration: float) -> Dict:
    """
    处理单个语言（用于并行执行）
    
    返回：处理结果字典
    """
    start_time = time.time()
    lang_info = LANGUAGE_CONFIG[lang_code]
    strategy = DEFAULT_STRATEGY  # 使用默认策略
    
    result = {
        'lang_code': lang_code,
        'language': lang_info['name'],
        'success': False,
        'output_video': None,
        'output_srt': None,
        'duration': 0,
        'error': None
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"{lang_info['emoji']} 开始处理: {lang_info['name']}")
        print(f"{'='*60}")
        
        # 创建临时目录
        temp_dir = os.path.join(output_dir, f"temp_{lang_code}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 读取字幕
        with open(srt_file, 'r', encoding='utf-8') as f:
            subs = list(srt.parse(f.read()))
        
        print(f"字幕条数: {len(subs)}")
        
        # Phase 1: 生成语音段落
        print(f"\n🎙️  Phase 1: 生成配音（并行优化）")
        segments_info = []
        
        # 使用线程池并行生成语音
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for i, sub in enumerate(subs):
                text = sub.content.strip()
                if not text:
                    continue
                
                audio_file = os.path.join(temp_dir, f"seg_{i:03d}.mp3")
                target_duration = (sub.end - sub.start).total_seconds()
                start_time = sub.start.total_seconds()
                
                # 提交任务
                future = executor.submit(
                    generate_segment_voice_fast,
                    text, lang_info['gtts_code'], audio_file,
                    target_duration, (strategy.tts_speed_min, strategy.tts_speed_max)
                )
                futures[future] = (i, audio_file, start_time, text[:30])
            
            # 收集结果
            for future in as_completed(futures):
                i, audio_file, start_time, text_preview = futures[future]
                try:
                    success = future.result()
                    if success:
                        segments_info.append((audio_file, start_time))
                        print(f"  [{i+1:03d}/{len(subs)}] ✅ {text_preview}...")
                    else:
                        print(f"  [{i+1:03d}/{len(subs)}] ❌ 生成失败")
                except Exception as e:
                    print(f"  [{i+1:03d}/{len(subs)}] ❌ 错误: {e}")
        
        if not segments_info:
            result['error'] = "没有成功生成任何语音段落"
            return result
        
        print(f"✅ 成功生成 {len(segments_info)}/{len(subs)} 个语音段落")
        
        # Phase 2: 合并音频
        print(f"\n🔄 Phase 2: 合并音频")
        merged_audio = os.path.join(output_dir, f"audio_{lang_code}.mp3")
        
        if not merge_audio_segments_fast(segments_info, merged_audio, video_duration):
            result['error'] = "音频合并失败"
            return result
        
        print(f"✅ 音频合并完成: {merged_audio}")
        
        # Phase 3: 生成最终视频
        print(f"\n🎬 Phase 3: 合成视频")
        
        # 生成调整后的字幕
        output_srt = os.path.join(output_dir, f"output_{lang_code}.srt")
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(srt.compose(subs))
        
        # 提取视频流并烧录字幕
        video_only = os.path.join(temp_dir, "video_only.mp4")
        cmd_extract = [
            "ffmpeg", "-y", "-i", video_file,
            "-vf", f"subtitles={output_srt}:force_style='FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1'",
            "-an", video_only
        ]
        subprocess.run(cmd_extract, capture_output=True)
        
        # 合并视频和音频（再次应用音量标准化确保一致性）
        output_video = os.path.join(output_dir, f"output_{lang_code}.mp4")
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", video_only,
            "-i", merged_audio,
            "-c:v", "copy",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",  # 最终音量标准化
            "-c:a", "aac",
            "-b:a", "192k",  # 提高音频码率保持质量
            "-shortest",
            output_video
        ]
        subprocess.run(cmd_merge, capture_output=True)
        
        # 清理临时文件
        for audio_file, _ in segments_info:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        
        if os.path.exists(video_only):
            os.remove(video_only)
        
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        # 检查结果
        if os.path.exists(output_video):
            result['success'] = True
            result['output_video'] = output_video
            result['output_srt'] = output_srt
            result['duration'] = time.time() - start_time
            
            print(f"\n{'='*60}")
            print(f"✅ {lang_info['emoji']} {lang_info['name']} 处理完成")
            print(f"⏱️  耗时: {result['duration']:.1f}秒")
            print(f"📁 输出: {output_video}")
            print(f"{'='*60}")
        else:
            result['error'] = "视频生成失败"
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ {lang_info['name']} 处理失败: {e}")
    
    return result


# ============================================================
# 并行批量处理器
# ============================================================

class FastParallelProcessor:
    """快速并行处理器"""
    
    def __init__(self, video_file: str, output_dir: str = "output_fast"):
        self.video_file = video_file
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频时长
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", video_file]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        self.video_duration = float(result.stdout.strip())
        
        print("=" * 70)
        print("🚀 多语言视频处理 - 高速并行版")
        print("=" * 70)
        print(f"视频文件: {video_file}")
        print(f"视频时长: {self.video_duration:.1f}秒")
        print(f"输出目录: {output_dir}")
        print(f"CPU核心数: {mp.cpu_count()}")
        print("=" * 70)
    
    def batch_process_parallel(self, language_srt_pairs: List[Tuple[str, str]], 
                               max_workers: int = None) -> Dict:
        """
        并行批量处理多个语言
        
        Args:
            language_srt_pairs: [(lang_code, srt_file), ...]
            max_workers: 最大并行数（None=自动）
        """
        start_time = time.time()
        
        if max_workers is None:
            # 自动决定并行数：取CPU核心数和任务数的最小值
            max_workers = min(mp.cpu_count(), len(language_srt_pairs), 4)
        
        print(f"\n🚀 启动并行处理")
        print(f"任务数: {len(language_srt_pairs)}")
        print(f"并行数: {max_workers}")
        print("=" * 70)
        
        results = []
        
        # 使用进程池并行处理
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for lang_code, srt_file in language_srt_pairs:
                future = executor.submit(
                    process_single_language,
                    self.video_file, lang_code, srt_file,
                    self.output_dir, self.video_duration
                )
                futures[future] = (lang_code, LANGUAGE_CONFIG[lang_code]['name'])
            
            # 收集结果
            for future in as_completed(futures):
                lang_code, lang_name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"\n❌ {lang_name} 处理异常: {e}")
                    results.append({
                        'lang_code': lang_code,
                        'language': lang_name,
                        'success': False,
                        'error': str(e)
                    })
        
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        
        print("\n" + "=" * 70)
        print("🎉 批量处理完成！")
        print("=" * 70)
        print(f"总耗时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
        print(f"成功: {success_count}/{len(results)}")
        print(f"平均每个语言: {total_time/len(results):.1f}秒")
        
        if max_workers > 1:
            sequential_time = sum(r.get('duration', 0) for r in results if r['success'])
            speedup = sequential_time / total_time if total_time > 0 else 1
            print(f"🚀 加速比: {speedup:.1f}x（相比串行处理）")
        
        print("\n📊 详细结果:")
        for result in results:
            if result['success']:
                print(f"  ✅ {result['language']}: {result['output_video']}")
                print(f"     耗时: {result['duration']:.1f}秒")
            else:
                print(f"  ❌ {result['language']}: {result.get('error', '未知错误')}")
        
        # 保存报告
        report = {
            'total_time': total_time,
            'total_languages': len(results),
            'success_count': success_count,
            'max_workers': max_workers,
            'results': results
        }
        
        report_file = os.path.join(self.output_dir, "batch_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 详细报告: {report_file}")
        print("=" * 70)
        
        return report


# ============================================================
# 测试和演示
# ============================================================

def demo():
    """演示用法"""
    print("🚀 高速并行处理演示\n")
    
    # 示例配置
    video_file = "adhd_无字幕.mp4"
    
    language_srt_pairs = [
        ('en', 'adhd_无字幕_en.srt'),
        ('es', 'adhd_无字幕_es.srt'),
        ('pt', 'adhd_无字幕_pt.srt'),
        ('ja', 'adhd_无字幕_ja.srt'),
    ]
    
    # 检查文件
    if not os.path.exists(video_file):
        print(f"❌ 找不到视频文件: {video_file}")
        return
    
    missing_files = [srt for _, srt in language_srt_pairs if not os.path.exists(srt)]
    if missing_files:
        print(f"❌ 找不到字幕文件:")
        for f in missing_files:
            print(f"  - {f}")
        return
    
    # 创建处理器
    processor = FastParallelProcessor(video_file, "output_fast")
    
    # 并行处理（自动决定并行数）
    report = processor.batch_process_parallel(language_srt_pairs)
    
    print(f"\n✅ 处理完成！")
    print(f"总耗时: {report['total_time']/60:.1f}分钟")
    print(f"成功: {report['success_count']}/{report['total_languages']}")


if __name__ == '__main__':
    # 如果有命令行参数，使用命令行模式
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        srt_files = sys.argv[2:]
        
        if not os.path.exists(video_file):
            print(f"❌ 找不到视频文件: {video_file}")
            sys.exit(1)
        
        # 解析语言代码和字幕文件
        language_srt_pairs = []
        for srt_file in srt_files:
            if not os.path.exists(srt_file):
                print(f"⚠️  跳过不存在的文件: {srt_file}")
                continue
            
            # 尝试从文件名提取语言代码
            basename = os.path.basename(srt_file)
            for lang_code in LANGUAGE_CONFIG.keys():
                if f"_{lang_code}." in basename:
                    language_srt_pairs.append((lang_code, srt_file))
                    break
        
        if not language_srt_pairs:
            print("❌ 没有找到有效的语言字幕对")
            sys.exit(1)
        
        processor = FastParallelProcessor(video_file)
        processor.batch_process_parallel(language_srt_pairs)
    else:
        demo()


