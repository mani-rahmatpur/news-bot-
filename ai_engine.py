import os
from typing import Optional
from google import genai
from google.genai import types
from config import API_KEY, PROMPTS
import database

# راه‌اندازی کلاینت رسمی و تک‌محوره گوگل جمینای
client = genai.Client(api_key=API_KEY)


def process_news_with_ai(article_content: str) -> Optional[str]:
    """ارسال متن خام خبر به Gemini با انتخاب لحن داینامیک و مکانیزم ضد کرش سرور"""
    try:
        current_tone = database.get_setting("bot_tone")
        selected_prompt = PROMPTS.get(current_tone, PROMPTS["official"])

        config = types.GenerateContentConfig(
            system_instruction=selected_prompt,
            temperature=0.3,
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=article_content,
            config=config,
        )

        if response.text:
            approx_tokens = len(article_content) // 4 + len(response.text) // 4
            database.update_stats(approx_tokens)
            return str(response.text)
        return None


    except Exception as ai_err:

        print(ai_err)

        try:

            import main

            main.diagnostic["gemini"] = str(ai_err)

        except:

            pass

        return None


def generate_image_with_ai(article_title: str) -> Optional[bytes]:
    """تولید عکس اختصاصی متناسب با تیتر خبر با مکانیزم بازیابی خودکار در صورت محدودیت API"""
    try:
        print(f"[AI IMAGE] در حال تولید عکس اختصاصی با جمینای برای خبر: {article_title}")
        image_prompt = f"A high-quality, modern, cinematic, and clean conceptual digital art or tech illustration representing this topic: {article_title}. Professional technology journalism style, 16:9 aspect ratio."

        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9",
                person_generation="DONT_ALLOW"
            )
        )
        for generated_image in result.generated_images:
            return generated_image.image.image_bytes
        return None
    except Exception as img_err:
        # اگر لایه تصویرساز به خاطر محدودیت اکانت رایگان خطا داد، سیستم رد می‌شود تا خبر بدون عکس یا با عکس سایت فرستاده شود
        print(f"[RECOVERY] خطا در تصویرساز هوش مصنوعی: {img_err}. سیستم به تصویر پشتیبان سوئیچ می‌کند.")
        return None
