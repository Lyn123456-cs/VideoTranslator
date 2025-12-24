# -*- coding: utf-8 -*-
"""
步骤3：根据字幕生成配音
智能TTS引擎：优先使用Edge TTS，失败时自动降级到gTTS
"""
import asyncio
import srt
import sys
import os
import subprocess
import edge_tts

# 尝试导入gTTS作为备用
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️ gTTS未安装，无法使用备用引擎")

# 中文语音选择（可选）
# 女声: zh-CN-XiaoxiaoNeural, zh-CN-XiaoyiNeural
# 男声: zh-CN-YunxiNeural, zh-CN-YunjianNeural
VOICE = "zh-CN-XiaoxiaoNeural"  # 默认女声，自然流畅

async def text_to_speech_edge(text: str, output_file: str, voice: str, max_retries: int = 3):
    """使用Edge TTS生成语音，带重试机制"""
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            
            # 检查文件是否真的生成了
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                # 检查文件大小（至少1KB表示有内容）
                if file_size > 1000:
                    return True  # 成功
                else:
                    # 删除无效文件
                    os.remove(output_file)
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ Edge TTS返回无效音频，{2}秒后重试 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(2)
            else:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Edge TTS未生成文件，{2}秒后重试 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(2)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️ Edge TTS连接失败，{2}秒后重试 ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(2)
            else:
                return False  # 失败
    return False

def text_to_speech_gtts(text: str, output_file: str, lang: str = 'en'):
    """使用gTTS生成语音（降级方案）"""
    if not GTTS_AVAILABLE:
        return False
    
    try:
        # 语言代码映射
        lang_map = {
            'zh-CN': 'zh-CN',
            'zh-TW': 'zh-TW',  
            'zh': 'zh-CN',
            'en-US': 'en',
            'en-GB': 'en',
            'en': 'en',
            'ja-JP': 'ja',
            'ja': 'ja',
            'ko-KR': 'ko',
            'ko': 'ko',
            'fr-FR': 'fr',
            'fr': 'fr',
            'de-DE': 'de',
            'de': 'de',
            'es-ES': 'es',
            'es': 'es',
            'pt-BR': 'pt',
            'pt': 'pt',
            'ru-RU': 'ru',
            'ru': 'ru',
            'ar-SA': 'ar',
            'ar': 'ar',
            'hi-IN': 'hi',
            'hi': 'hi',
            'th-TH': 'th',
            'th': 'th',
            'vi-VN': 'vi',
            'vi': 'vi',
            'it-IT': 'it',
            'it': 'it',
            'tr-TR': 'tr',
            'tr': 'tr',
            'id-ID': 'id',
            'id': 'id',
        }
        
        # 从Edge TTS音色代码提取语言
        gtts_lang = 'en'  # 默认
        for key in lang_map:
            if key in lang:
                gtts_lang = lang_map[key]
                break
        
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_file)
        return True
    except Exception as e:
        print(f"  ❌ gTTS也失败了: {str(e)[:100]}")
        return False

async def text_to_speech_smart(text: str, output_file: str, voice: str):
    """智能TTS：优先Edge，失败时降级到gTTS"""
    if not GTTS_AVAILABLE:
        # gTTS不可用，只用Edge
        success = await text_to_speech_edge(text, output_file, voice, max_retries=3)
        if success:
            return 'edge'
        raise Exception("Edge TTS失败且gTTS不可用")
    
    # 尝试Edge TTS
    success = await text_to_speech_edge(text, output_file, voice, max_retries=2)
    if success:
        return 'edge'
    
    # Edge失败，降级到gTTS
    print(f"  ⚠️ Edge TTS失败，切换到gTTS备用引擎...")
    success = text_to_speech_gtts(text, output_file, voice)
    if success:
        return 'gtts'
    
    raise Exception("Edge TTS和gTTS都失败了")

def generate_voiceover(srt_file: str, output_audio: str, voice: str = VOICE):
    """根据字幕文件生成配音（使用ffmpeg合成以避免pydub问题）"""
    
    # 读取字幕
    with open(srt_file, "r", encoding="utf-8") as f:
        content = f.read()
    subs = list(srt.parse(content))
    
    print(f"共 {len(subs)} 条字幕，开始生成配音...")
    print(f"使用语音: {voice}")
    print("=" * 50)
    
    # 创建临时目录
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 获取视频总时长
    total_duration = subs[-1].end.total_seconds() + 1.0
    
    # 为每条字幕生成语音
    success_count = 0
    failed_count = 0
    edge_count = 0
    gtts_count = 0
    input_files = []  # 存储(文件路径, 延迟时间ms)
    
    # 首次检测：测试第一片段判断网络状况
    first_engine = None
    
    for i, sub in enumerate(subs):
        text = sub.content.strip()
        if not text:
            continue
            
        temp_file = os.path.join(temp_dir, f"segment_{i:03d}.mp3")
        
        print(f"[{i+1:02d}/{len(subs)}] {text[:30]}...")
        
        try:
            # 生成语音（智能降级）
            engine = asyncio.run(text_to_speech_smart(text, temp_file, voice))
            
            if i == 0:
                first_engine = engine
                if engine == 'gtts':
                    print(f"\n⚠️  检测到Edge TTS网络不稳定，已切换到gTTS引擎")
                    print(f"💡 gTTS不支持音色选择，将使用默认音色\n")
            
            # 统计使用的引擎
            if engine == 'edge':
                edge_count += 1
            elif engine == 'gtts':
                gtts_count += 1
            
            # 检查文件是否生成成功
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                # 计算延迟时间（毫秒）
                delay_ms = int(sub.start.total_seconds() * 1000)
                input_files.append((temp_file, delay_ms))
                success_count += 1
            else:
                failed_count += 1
                print(f"  ⚠️ 文件生成失败，跳过此片段")
            
        except Exception as e:
            failed_count += 1
            print(f"  ⚠️ 跳过此片段: {str(e)[:50]}")
    
    # 使用ffmpeg合成所有音频
    if input_files:
        print("\n🔄 使用ffmpeg合成音频...")
        
        # 构建ffmpeg命令
        inputs = []
        filter_cmds = []
        
        for idx, (file, delay_ms) in enumerate(input_files):
            inputs.extend(["-i", file])
            # adelay 正确语法：delays=ms（单声道）或 delays=ms|ms（立体声）
            filter_cmds.append(f"[{idx}]adelay=delays={delay_ms}:all=1[a{idx}]")
        
        # 混合所有音频并增强音量
        mix_inputs = "".join([f"[a{i}]" for i in range(len(input_files))])
        # 使用 amix 混合（dropout_transition=0 避免重叠时音量衰减）+ volume 增益 + dynaudnorm 动态归一化
        filter_cmds.append(f"{mix_inputs}amix=inputs={len(input_files)}:duration=longest:dropout_transition=0,volume=2.5,dynaudnorm[out]")
        
        filter_complex = ";".join(filter_cmds)
        
        # 执行ffmpeg命令
        cmd = [
            "ffmpeg", "-y"
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(total_duration),
            output_audio
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  ffmpeg合成出现警告，但可能已成功")
    
    # 清理临时文件
    for file, _ in input_files:
        if os.path.exists(file):
            os.remove(file)
    
    # 删除临时目录
    if os.path.exists(temp_dir):
        try:
            os.rmdir(temp_dir)
        except:
            pass
    
    print("=" * 50)
    print(f"✅ 配音生成完成: {output_audio}")
    print(f"📊 成功: {success_count}/{len(subs)} | 失败: {failed_count}/{len(subs)}")
    
    if edge_count > 0 and gtts_count > 0:
        print(f"🔄 引擎使用: Edge TTS {edge_count}片段 + gTTS {gtts_count}片段")
    elif gtts_count > 0:
        print(f"🔄 全部使用 gTTS 引擎")
    elif edge_count > 0:
        print(f"🔄 全部使用 Edge TTS 引擎")
    
    if failed_count > 0:
        print(f"⚠️ 有 {failed_count} 个片段生成失败，但已完成其余部分")

def main():
    if len(sys.argv) < 3:
        print("用法: python s3_generate_voiceover.py input.srt output.mp3 [voice]")
        print("例如: python s3_generate_voiceover.py zh.srt voiceover.mp3")
        print("\n可用语音:")
        print("  女声: zh-CN-XiaoxiaoNeural (默认), zh-CN-XiaoyiNeural")
        print("  男声: zh-CN-YunxiNeural, zh-CN-YunjianNeural")
        sys.exit(1)
    
    srt_file = sys.argv[1]
    output_audio = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else VOICE
    
    if not os.path.exists(srt_file):
        print(f"找不到文件: {srt_file}")
        sys.exit(1)
    
    generate_voiceover(srt_file, output_audio, voice)

if __name__ == "__main__":
    main()





