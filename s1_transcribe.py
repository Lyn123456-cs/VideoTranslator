# -*- coding: utf-8 -*-
"""
智能语音识别脚本 - 自动检测并使用最佳引擎
优先使用 Faster-Whisper（快5倍），如果没有则回退到标准 Whisper
"""
import os
import subprocess
import sys

# 尝试导入 Faster-Whisper，如果失败则使用标准 Whisper
try:
    from faster_whisper import WhisperModel
    USE_FASTER = True
    print("✅ 使用 Faster-Whisper（速度快5倍）")
except ImportError:
    import whisper
    from whisper.utils import get_writer
    USE_FASTER = False
    print("⚠️  使用标准 Whisper（如需加速，请安装 faster-whisper）")

def extract_audio(input_video, audio_path="audio_tmp.wav"):
    """从视频提取音频"""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        audio_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path

def format_timestamp(seconds):
    """转换秒数为 SRT 时间格式 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def transcribe_with_faster_whisper(audio_path, model_size="small", output_srt="original.srt"):
    """使用 Faster-Whisper 转录"""
    print(f"加载 Faster-Whisper 模型：{model_size}（首次可能会比较慢）")
    
    # 加载模型 - CPU 使用 int8 量化以提高速度
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print("开始转录音频并自动识别语言...")
    segments, info = model.transcribe(
        audio_path,
        task="transcribe",
        beam_size=5,
        vad_filter=True,  # 启用 VAD 过滤
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"✅ 检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
    
    # 转换为列表以便多次使用
    segments_list = list(segments)
    
    # 写入 SRT 文件
    print(f"正在写入字幕文件: {output_srt}")
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments_list, start=1):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()
            
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    
    print(f"✅ 字幕已保存到: {output_srt}")
    return output_srt

def transcribe_with_standard_whisper(audio_path, model_size="small", output_srt="original.srt"):
    """使用标准 Whisper 转录"""
    print(f"加载 Whisper 模型：{model_size}（首次可能会比较慢）")
    model = whisper.load_model(model_size)

    print("开始转录音频并自动识别语言...")
    result = model.transcribe(audio_path, task="transcribe", verbose=True)

    print(f"✅ 检测到语言: {result['language']}")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_srt)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 使用 whisper 自带的 SRT writer
    # writer会在output_dir目录下生成与audio_path同名的.srt文件
    writer = get_writer("srt", output_dir or ".")
    writer(result, audio_path, {"max_line_width": None, "max_line_count": None, "highlight_words": False})
    
    # Whisper生成的文件名基于audio_path
    audio_basename = os.path.basename(audio_path).replace(".wav", ".srt")
    auto_srt = os.path.join(output_dir or ".", audio_basename)
    
    # 重命名到目标文件
    if os.path.exists(auto_srt):
        if auto_srt != output_srt:
            # 如果目标文件已存在，先删除
            if os.path.exists(output_srt):
                os.remove(output_srt)
            os.rename(auto_srt, output_srt)
            print(f"✅ 字幕已保存到: {output_srt}")
        else:
            print(f"✅ 字幕已保存到: {output_srt}")
    else:
        print(f"⚠️  自动生成的字幕文件不存在: {auto_srt}")
        print(f"   输出目录: {output_dir or '.'}")
        print(f"   audio_path: {audio_path}")
    
    return output_srt

def transcribe_audio_to_srt(audio_path, model_size="small", output_srt="original.srt"):
    """智能选择转录引擎"""
    if USE_FASTER:
        return transcribe_with_faster_whisper(audio_path, model_size, output_srt)
    else:
        return transcribe_with_standard_whisper(audio_path, model_size, output_srt)

def extract_subtitles(input_video, output_srt="original.srt", model_size="small"):
    """
    从视频中提取字幕（供GUI调用）
    
    Args:
        input_video: 输入视频路径
        output_srt: 输出字幕路径
        model_size: 模型大小（tiny, base, small, medium, large）
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        # 提取音频
        audio_path = extract_audio(input_video)
        
        # 转录
        transcribe_audio_to_srt(audio_path, model_size, output_srt)
        
        # 清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # 检查输出文件是否存在
        return os.path.exists(output_srt)
    except Exception as e:
        print(f"❌ 转录失败: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python s1_transcribe.py <输入视频> <输出字幕.srt> [模型大小]")
        print("模型大小: tiny, base, small, medium, large")
        sys.exit(1)

    input_video = sys.argv[1]
    output_srt = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "small"

    print("=" * 60)
    print(f"🎬 VideoTranslator - 字幕提取 ({'Faster-Whisper' if USE_FASTER else 'Standard Whisper'})")
    print("=" * 60)
    print(f"输入视频: {input_video}")
    print(f"输出字幕: {output_srt}")
    print(f"模型大小: {model_size}")
    print("=" * 60)

    # 提取音频
    print("\n📝 步骤1: 提取音频...")
    audio_path = extract_audio(input_video)
    print(f"✅ 音频已提取: {audio_path}")

    # 转录
    print(f"\n📝 步骤2: 语音识别...")
    transcribe_audio_to_srt(audio_path, model_size, output_srt)

    # 清理临时文件
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"🧹 已清理临时文件: {audio_path}")

    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
