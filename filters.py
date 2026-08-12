import re


# ============================================================
# Crypto
# ============================================================

CRYPTO_KEYWORDS = [
    "bitcoin",
    "ethereum",
    "crypto",
    "cryptocurrency",
    "blockchain",
    "web3",
    "nft",
    "token",
    "defi",
]


# ============================================================
# Artificial Intelligence
# ============================================================

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "generative ai",
    "machine learning",
    "deep learning",
    "llm",
    "large language model",
    "language model",
    "gpt",
    "chatgpt",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "copilot",
]


# ============================================================
# General Technology
# ============================================================

TECH_KEYWORDS = [
    "technology",
    "tech",
    "software",
    "hardware",
    "developer",
    "programming",
    "coding",
    "computer",
    "processor",
    "cpu",
    "gpu",
    "chip",
    "chips",
    "semiconductor",
    "operating system",
    "linux",
    "windows",
    "android",
    "ios",
    "apple",
    "microsoft",
    "google",
]


# ============================================================
# Cloud / Data
# ============================================================

CLOUD_DATA_KEYWORDS = [
    "cloud",
    "cloud computing",
    "cloud infrastructure",
    "aws",
    "azure",
    "google cloud",
    "data center",
    "data centre",
    "database",
    "data breach",
]


# ============================================================
# Security
# ============================================================

SECURITY_KEYWORDS = [
    "security",
    "cybersecurity",
    "cyber security",
    "hack",
    "hacker",
    "hacking",
    "malware",
    "ransomware",
    "phishing",
    "vulnerability",
    "exploit",
    "zero-day",
    "0-day",
    "data breach",
    "privacy",
]


# ============================================================
# Robotics / Automation
# ============================================================

ROBOTICS_KEYWORDS = [
    "robot",
    "robots",
    "robotics",
    "humanoid",
    "autonomous",
    "automation",
    "drone",
    "robotaxi",
]


# ============================================================
# Startup / Business Technology
# ============================================================

STARTUP_BUSINESS_KEYWORDS = [
    "startup",
    "startups",
    "venture",
    "funding",
    "fundraising",
    "acquisition",
    "investment",
    "valuation",
    "enterprise",
    "saas",
]


# ============================================================
# Block / Reject Keywords
#
# این کلمات فقط روی TITLE بررسی می‌شوند.
# ============================================================

BLOCK_KEYWORDS = [
    "price",
    "pricing",
    "buy",
    "buying guide",
    "purchase",
    "deal",
    "deals",
    "discount",
    "best phone",
    "best phones",
    "best laptop",
    "best laptops",
    "budget phone",
    "budget phones",
    "budget laptop",
    "budget laptops",
    "price comparison",
]


# ============================================================
# همه کلیدواژه‌های تکنولوژی
# ============================================================

ALL_TECH_KEYWORDS = (
    CRYPTO_KEYWORDS
    + AI_KEYWORDS
    + TECH_KEYWORDS
    + CLOUD_DATA_KEYWORDS
    + SECURITY_KEYWORDS
    + ROBOTICS_KEYWORDS
    + STARTUP_BUSINESS_KEYWORDS
)


# ============================================================
# نرمال‌سازی متن
# ============================================================

def normalize_text(text: str) -> str:
    """
    نرمال‌سازی ساده برای جست‌وجوی دقیق‌تر.
    """

    if not text:
        return ""

    text = text.lower()

    # حذف فاصله‌های اضافی
    text = re.sub(r"\s+", " ", text)

    # تبدیل بعضی علائم به فاصله
    text = re.sub(r"[_/|]+", " ", text)

    return text.strip()


# ============================================================
# تطبیق کلمه یا عبارت
# ============================================================

def keyword_matches(text: str, keyword: str) -> bool:
    """
    بررسی دقیق یک keyword.

    برای کلمات کوتاه مثل:
        ai
        cpu
        gpu
        aws

    از word boundary استفاده می‌کنیم تا
    داخل کلمات دیگر match نشوند.

    برای عبارت‌های چندکلمه‌ای نیز
    همین روش تا حد زیادی از false positive جلوگیری می‌کند.
    """

    text = normalize_text(text)
    keyword = normalize_text(keyword)

    if not text or not keyword:
        return False

    escaped_keyword = re.escape(keyword)

    pattern = rf"(?<![a-z0-9]){escaped_keyword}(?![a-z0-9])"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE
    ) is not None


# ============================================================
# تشخیص زبان انگلیسی
# ============================================================

def is_english_text(text: str) -> bool:
    """
    جلوگیری از ورود محتوای فارسی یا غیرانگلیسی.

    منبع باید عمدتاً انگلیسی باشد.
    """

    if not text:
        return False

    persian_chars = 0
    latin_chars = 0

    for char in text:

        if (
            "\u0600"
            <= char
            <= "\u06FF"
        ):
            persian_chars += 1

        elif (
            "a"
            <= char.lower()
            <= "z"
        ):
            latin_chars += 1

    # برای متن بسیار کوتاه
    if latin_chars < 20:
        return False

    # اگر متن فارسی قابل‌توجهی داشته باشد
    if persian_chars > 20:
        return False

    # نسبت حروف انگلیسی به فارسی
    total_letters = (
        latin_chars
        + persian_chars
    )

    if total_letters == 0:
        return False

    english_ratio = (
        latin_chars
        / total_letters
    )

    return english_ratio >= 0.85


# ============================================================
# تشخیص ارتباط تکنولوژیک
# ============================================================

def is_technology_relevant(
    title: str,
    content: str
) -> bool:
    """
    بررسی می‌کند آیا خبر:
    1. انگلیسی است
    2. خبر خرید / قیمت / راهنمای خرید نیست
    3. حداقل در یکی از حوزه‌های فناوری قرار دارد
    """

    title = title or ""
    content = content or ""

    normalized_title = normalize_text(title)
    normalized_content = normalize_text(content)

    full_text = (
        f"{normalized_title} "
        f"{normalized_content}"
    ).strip()

    # ========================================================
    # 1. زبان
    # ========================================================

    if not is_english_text(full_text):

        print(
            f"[FILTER NON-ENGLISH] {title}"
        )

        return False

    # ========================================================
    # 2. حذف خبرهای خرید / قیمت
    #
    # فقط TITLE بررسی می‌شود تا عباراتی که در متن مقاله
    # آمده‌اند باعث حذف اشتباه خبر نشوند.
    # ========================================================

    for keyword in BLOCK_KEYWORDS:

        if keyword_matches(
            normalized_title,
            keyword
        ):

            print(
                f"[FILTER BLOCK] "
                f"{keyword} -> {title}"
            )

            return False

    # ========================================================
    # 3. بررسی حوزه‌های تکنولوژی
    # ========================================================

    for keyword in ALL_TECH_KEYWORDS:

        if keyword_matches(
            full_text,
            keyword
        ):

            print(
                f"[FILTER MATCH] "
                f"{keyword} -> {title}"
            )

            return True

    # ========================================================
    # 4. بدون تطابق
    # ========================================================

    print(
        f"[FILTER NO MATCH] {title}"
    )

    return False
