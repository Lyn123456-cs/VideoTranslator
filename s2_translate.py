# -*- coding: utf-8 -*-
import sys
import srt
import time
from googletrans import Translator

def translate_text(text: str, target_lang: str, max_retries: int = 3) -> tuple:
    """
    使用 Google 翻译 API 翻译文本（带重试机制）
    
    返回：(翻译文本, 是否成功)
    """
    # 完整的语言代码映射
    lang_map = {
        'zh': 'zh-cn',   # 中文
        'en': 'en',      # 英语
        'ja': 'ja',      # 日语
        'ko': 'ko',      # 韩语
        'es': 'es',      # 西班牙语
        'pt': 'pt',      # 葡萄牙语
        'fr': 'fr',      # 法语
        'de': 'de',      # 德语
        'hi': 'hi',      # 印地语
        'vi': 'vi',      # 越南语
        'ru': 'ru',      # 俄语
        'ar': 'ar',      # 阿拉伯语
        'it': 'it',      # 意大利语
        'th': 'th',      # 泰语
    }
    dest = lang_map.get(target_lang, target_lang)
    
    for attempt in range(max_retries):
        try:
            # 每次重试都创建新的翻译器实例
            translator = Translator()
            result = translator.translate(text, dest=dest)
            
            if result and result.text:
                return result.text, True
            else:
                print(f"  ⚠️  翻译返回空结果，重试 {attempt + 1}/{max_retries}")
                time.sleep(1)
                
        except Exception as e:
            print(f"  ⚠️  翻译出错 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                print(f"  ❌ 翻译失败，已重试{max_retries}次")
                return text, False  # 返回原文和失败状态
    
    return text, False

def translate_srt(input_srt: str, output_srt: str, target_lang: str) -> bool:
    """
    翻译SRT字幕文件
    
    返回：是否成功
    """
    try:
        with open(input_srt, "r", encoding="utf-8") as f:
            content = f.read()

        subs = list(srt.parse(content))
        new_subs = []
        failed_count = 0

        print(f"开始翻译 {len(subs)} 条字幕到 {target_lang}...")

        for sub in subs:
            original_text = sub.content.strip()
            if not original_text:
                new_subs.append(sub)
                continue
            
            # 调用翻译函数（带重试）
            translated_text, success = translate_text(original_text, target_lang)
            
            if not success:
                failed_count += 1
            
            # 显示进度（简化输出）
            if sub.index % 5 == 0 or not success:
                preview = original_text[:20] + "..." if len(original_text) > 20 else original_text
                status = "✅" if success else "❌"
                print(f"  [{sub.index}/{len(subs)}] {status} {preview}")
            
            new_sub = srt.Subtitle(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                content=translated_text
            )
            new_subs.append(new_sub)
            
            # 避免请求过快
            time.sleep(0.1)

        # 保存翻译结果
        result = srt.compose(new_subs)
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write(result)

        if failed_count > 0:
            print(f"⚠️  翻译完成，但有 {failed_count}/{len(subs)} 条失败（使用原文）")
            print(f"✅ 已生成字幕：{output_srt}")
            return True  # 部分成功也算成功
        else:
            print(f"✅ 翻译完成：{output_srt}")
            return True
            
    except Exception as e:
        print(f"❌ 翻译过程出错: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("用法：python step2_translate_srt.py original.srt translated.srt target_lang")
        print("例如：python step2_translate_srt.py original.srt zh.srt zh")
        sys.exit(1)

    input_srt = sys.argv[1]
    output_srt = sys.argv[2]
    target_lang = sys.argv[3]

    translate_srt(input_srt, output_srt, target_lang)

if __name__ == "__main__":
    main()
