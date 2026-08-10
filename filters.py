CRYPTO_KEYWORDS = [
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "crypto",
    "cryptocurrency",
    "blockchain",
    "web3",
    "nft",
    "token",
    "defi",
    "متاورس",
    "بلاکچین",
    "ارز دیجیتال",
    "رمزارز",
    "رمز ارز",
    "بیت کوین",
    "اتریوم",
]


AI_KEYWORDS = [
    "artificial intelligence",
    "artificial intelligence",
    "ai",
    "openai",
    "chatgpt",
    "gemini",
    "claude",
    "grok",
    "llm",
    "machine learning",
    "deep learning",
    "generative ai",
    "هوش مصنوعی",
    "یادگیری ماشین",
    "یادگیری عمیق",
    "مدل زبانی",
    "مدل هوش مصنوعی",
    "عامل هوش مصنوعی",
    "ایجنت هوش مصنوعی",
]


TECH_KEYWORDS = [
    "chip",
    "chips",
    "processor",
    "gpu",
    "cpu",
    "npu",
    "semiconductor",
    "cybersecurity",
    "cyber security",
    "hacking",
    "hack",
    "cloud",
    "cloud computing",
    "data center",
    "datacenter",
    "robot",
    "robotics",
    "space",
    "spacex",
    "starship",
    "مایکروسافت",
    "اپل",
    "گوگل",
    "پردازنده",
    "پردازنده گرافیکی",
    "تراشه",
    "تراشه‌ها",
    "نیمه‌رسانا",
    "امنیت سایبری",
    "هک",
    "ربات",
    "رباتیک",
    "کلاد",
    "رایانش ابری",
    "دیتاسنتر",
]


# موضوعاتی که معمولاً برای کانال ما مناسب نیستند
# مخصوصاً اخبار خرید، قیمت و بررسی محصول
SHOPPING_KEYWORDS = [
    "قیمت",
    "خرید",
    "راهنمای خرید",
    "بهترین گوشی",
    "بهترین لپ تاپ",
    "بهترین لپتاپ",
    "گوشی اقتصادی",
    "لپ تاپ اقتصادی",
    "لپتاپ اقتصادی",
    "بررسی قیمت",
    "مقایسه قیمت",
    "تخفیف",
    "فروش ویژه",
    "اقساط",
]


# این کلمات به تنهایی نباید باعث حذف شوند.
# فقط زمانی حذف می‌کنیم که موضوع خبر واقعاً محصول مصرفی باشد.
CONSUMER_PRODUCT_KEYWORDS = [
    "گوشی",
    "موبایل",
    "لپ تاپ",
    "لپتاپ",
    "تبلت",
    "ساعت هوشمند",
    "هدفون",
    "ایرباد",
    "شارژر",
]


def _contains_keyword(text, keywords):
    for keyword in keywords:
        if keyword.lower() in text:
            return True
    return False


def is_technology_relevant(title, content):

    title = title or ""
    content = content or ""

    title_lower = title.lower()
    content_lower = content.lower()

    text = f"{title_lower} {content_lower}"

    # -------------------------------------------------
    # 1. حذف مستقیم اخبار خرید / قیمت / تخفیف
    # -------------------------------------------------

    if _contains_keyword(title_lower, SHOPPING_KEYWORDS):
        return False

    # -------------------------------------------------
    # 2. اخبار Crypto همیشه اولویت دارند
    # -------------------------------------------------

    if _contains_keyword(text, CRYPTO_KEYWORDS):
        return True

    # -------------------------------------------------
    # 3. اخبار AI
    # -------------------------------------------------

    if _contains_keyword(text, AI_KEYWORDS):
        return True

    # -------------------------------------------------
    # 4. اخبار تکنولوژی زیرساختی
    # -------------------------------------------------

    if _contains_keyword(text, TECH_KEYWORDS):

        # اگر خبر صرفاً درباره محصول مصرفی باشد
        # ولی موضوع تکنولوژیک جدی نداشته باشد، حذف شود.

        if _contains_keyword(title_lower, CONSUMER_PRODUCT_KEYWORDS):

            # اگر در عنوان محصول مصرفی آمده ولی
            # همزمان AI / Crypto / Tech واقعی دارد،
            # اجازه عبور می‌دهیم.

            if (
                _contains_keyword(text, AI_KEYWORDS)
                or _contains_keyword(text, CRYPTO_KEYWORDS)
                or _contains_keyword(text, [
                    "chip",
                    "processor",
                    "gpu",
                    "cpu",
                    "npu",
                    "semiconductor",
                    "تراشه",
                    "پردازنده",
                    "نیمه‌رسانا",
                ])
            ):
                return True

            return False

        return True

    # -------------------------------------------------
    # 5. در غیر این صورت خبر نامرتبط است
    # -------------------------------------------------

    return False
