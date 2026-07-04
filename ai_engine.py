from typing import Any, List
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from config import API_KEY, CUSTOM_SYSTEM_PROMPT

# راه‌اندازی کلاینت OpenAI
client: OpenAI = OpenAI(api_key=API_KEY)


def process_news_with_ai(article_content: str) -> Any:
    """ارسال متن خام خبر به API چت‌جی‌پتی و دریافت پاسخ خلاصه‌شده"""
    try:
        # تنظیم ساختار پیام‌ها برای رفع خطاهای Type hinting در ادیتور
        messages_payload: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": CUSTOM_SYSTEM_PROMPT},
            {"role": "user", "content": article_content}
        ]

        # ارسال درخواست به مدل به‌صرفه و سریع gpt-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_payload,
            temperature=0.3,
            stream=False
        )

        # بررسی وجود پاسخ و استخراج متن آن
        if hasattr(response, 'choices') and len(response.choices) > 0:
            return response.choices.message.content
        return None

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None
