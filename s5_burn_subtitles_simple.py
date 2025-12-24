# -*- coding: utf-8 -*-
"""简化版字幕烧录工具"""
import sys, subprocess, os

video, srt, output, audio = sys.argv[1:5]
pos = "--bottom" in sys.argv and "2" or "--top" in sys.argv and "8" or "2"

print(f"🎬 合成视频: {output}")

# 方案：分两步处理，确保不会有双音轨
# 步骤1：创建无音频的视频（带字幕）
temp_video = output.replace('.mp4', '_temp_nosound.mp4')
cmd1 = f'ffmpeg -i "{video}" -an -vf "subtitles={srt}:force_style=\'Alignment={pos},MarginV=30,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2\'" -c:v libx264 "{temp_video}" -y'
result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)

if result1.returncode != 0:
    print(f"❌ 步骤1失败: {result1.stderr}")
    sys.exit(1)

# 步骤2：将配音添加到无音频的视频
cmd2 = f'ffmpeg -i "{temp_video}" -i "{audio}" -map 0:v -map 1:a -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy -c:a aac -shortest "{output}" -y'
result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)

# 删除临时文件
if os.path.exists(temp_video):
    os.remove(temp_video)

if result2.returncode != 0:
    print(f"❌ 步骤2失败: {result2.stderr}")
    sys.exit(1)

print(f"✅ 完成: {output}")
