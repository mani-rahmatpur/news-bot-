import time
from typing import Optional

from google import genai
from google.genai import types

from config import API_KEY, PROMPTS
import database


# ============================================================
# Gemini Client
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# وضعیت محدودیت Gemini
# ============================================================

GEMINI_QUOTA_BLOCKED_UNTIL = 0
GEMINI_QUOTA_COOLDOWN = 120




# ============================================================
# Exception مخصوص سهمیه Gemini
# ============================================================

class GeminiQuotaExceeded(Exception):
    """
    زمانی ایجاد می‌شود که Gemini به دلیل quota
    یا rate limit درخواست را رد کند.
    """
    pass


def is_gemini_available() -> bool:
    """
    بررسی می‌کند آیا Gemini در حال حاضر اجازه درخواست دارد یا خیر.
    """

    return time.time() >= GEMINI_QUOTA_BLOCKED_UNTIL


# ============================================================
# Text Generation
# ============================================================

def process_news_with_ai(
    article_content: str
) -> Optional[str]:

    global GEMINI_QUOTA_BLOCKED_UNTIL

    # ========================================================
    # بررسی cooldown
    # ========================================================

    now = time.time()

    if now < GEMINI_QUOTA_BLOCKED_UNTIL:

        remaining = int(
            GEMINI_QUOTA_BLOCKED_UNTIL - now
        )

        print(
            f"[AI QUOTA BLOCKED] "
            f"Gemini temporarily blocked. "
            f"Retry in {remaining}s."
        )

        raise GeminiQuotaExceeded()

    # ========================================================
    # دریافت لحن فعلی
    # ========================================================

    try:

        current_tone = database.get_setting(
            "bot_tone"
        )

        selected_prompt = PROMPTS.get(
            current_tone,
            PROMPTS["official"]
        )

        config = types.GenerateContentConfig(
            system_instruction=selected_prompt,
            temperature=0.3,
        )

        # ====================================================
        # درخواست به Gemini
        # ====================================================

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=article_content,
            config=config,
        )

        # ====================================================
        # پاسخ موفق
        # ====================================================

        if response.text:

            approx_tokens = (
                len(article_content) // 4
                + len(response.text) // 4
            )

            database.update_stats(
                approx_tokens
            )

            print(
                "[AI SUCCESS] "
                "Gemini response received."
            )

            return str(
                response.text
            )

        # ====================================================
        # پاسخ خالی
        # ====================================================

        print(
            "[AI EMPTY] "
            "Gemini returned an empty response."
        )

        return None

    except Exception as ai_err:

        error_text = str(
            ai_err
        )

        # ====================================================
        # تشخیص quota / rate limit
        # ====================================================

        if (
            "RESOURCE_EXHAUSTED"
            in error_text
            or "quota"
            in error_text.lower()
            or "rate limit"
            in error_text.lower()
        ):

            # -----------------------------------------------
            # فعال کردن cooldown
            # -----------------------------------------------

            GEMINI_QUOTA_BLOCKED_UNTIL = (
                time.time()
                + GEMINI_QUOTA_COOLDOWN
            )

            print(
                "[AI QUOTA] "
                "Gemini quota/rate limit exceeded."
            )

            print(
                f"[AI QUOTA] "
                f"Queue paused for "
                f"{GEMINI_QUOTA_COOLDOWN}s."
            )

            # -----------------------------------------------
            # انتقال مستقیم خطا به main.py
            # -----------------------------------------------

            raise GeminiQuotaExceeded()

        # ====================================================
        # سایر خطاهای AI
        # ====================================================

        print(
            f"[AI ERROR] {error_text}"
        )

        return None


# ============================================================
# AI Image Generation
# ============================================================

def generate_image_with_ai(
    article_title: str
) -> Optional[bytes]:

    try:

        print(
            "[AI IMAGE] "
            f"در حال تولید عکس اختصاصی با جمینای برای خبر: "
            f"{article_title}"
        )

        image_prompt = (
            "A high-quality, modern, cinematic, "
            "and clean conceptual digital art "
            "or technology illustration representing "
            f"this topic: {article_title}. "
            "Professional technology journalism style, "
            "16:9 aspect ratio."
        )

        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9",
                person_generation="DONT_ALLOW"
            )
        )

        # ====================================================
        # دریافت تصویر
        # ====================================================

        for generated_image in result.generated_images:

            if (
                generated_image.image
                and generated_image.image.image_bytes
            ):

                return (
                    generated_image
                    .image
                    .image_bytes
                )

        print(
            "[AI IMAGE EMPTY] "
            "No generated image returned."
        )

        return None

    except Exception as img_err:

        print(
            "[RECOVERY] "
            f"خطا در تصویرساز هوش مصنوعی: "
            f"{img_err}. "
            "سیستم به تصویر پشتیبان سوئیچ می‌کند."
        )

        return None
