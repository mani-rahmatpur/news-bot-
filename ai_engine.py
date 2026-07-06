import os
from typing import Optional
from google import genai
from google.genai import types
from config import API_KEY, PROMPTS
import database

# راه‌اندازی کلاینت رسمی گوگل
client = genai.Client(api_key=API_KEY)


def process_news_with_ai(article_content: str) -> Optional[str]:
    """ارسال متن خبر به Gemini با انتخاب لحن داینامیک از دیتابیس تنظیمات پنل ادمین"""
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
            # محاسبه تخمینی توکن مصرفی برای پنل گزارش وضعیت
            approx_tokens = len(article_content) // 4 + len(response.text) // 4
            database.update_stats(approx_tokens)
            return str(response.text)
        return None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
