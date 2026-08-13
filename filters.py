import re


# ============================================================
# Strong technology keywords
# ============================================================

STRONG_KEYWORDS = [

    # AI
    "artificial intelligence",
    "generative ai",
    "machine learning",
    "deep learning",
    "large language model",
    "language model",
    "llm",
    "gpt",
    "chatgpt",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "copilot",

    # Security
    "cybersecurity",
    "cyber security",
    "hacking",
    "hacker",
    "malware",
    "ransomware",
    "phishing",
    "vulnerability",
    "zero-day",
    "0-day",
    "data breach",
    "security breach",

    # Cloud / Infrastructure
    "cloud computing",
    "cloud infrastructure",
    "data center",
    "data centre",
    "server infrastructure",

    # Hardware
    "semiconductor",
    "semiconductors",
    "chip",
    "chips",
    "gpu",
    "cpu",
    "processor",

    # Robotics
    "robotics",
    "robot",
    "robots",
    "drone",
    "drones",
    "humanoid",
    "robotaxi",
    "autonomous robot",

    # Crypto / Web3
    "bitcoin",
    "ethereum",
    "cryptocurrency",
    "blockchain",
    "web3",
    "defi",
]


# ============================================================
# Medium technology keywords
# ============================================================

MEDIUM_KEYWORDS = [

    "ai",
    "robot",
    "robots",
    "drone",
    "drones",
    "autonomous",
    "automation",

    "cloud",
    "aws",
    "azure",
    "google cloud",

    "software",
    "hardware",
    "developer",
    "programming",
    "coding",
    "computer",
    "operating system",
    "linux",
    "windows",
    "android",
    "ios",

    "startup",
    "venture",

    "enterprise",
    "saas",

    "crypto",
    "token",
    "nft",

    "privacy",
    "security",
    "hack",
]


# ============================================================
# Business/context keywords
#
# این‌ها به تنهایی خبر فناوری محسوب نمی‌شوند.
# ============================================================

BUSINESS_KEYWORDS = [
    "funding",
    "fundraise",
    "fundraising",
    "investment",
    "valuation",
    "acquisition",
    "acquires",
    "acquired",
]


# ============================================================
# Block keywords
#
# فقط عنوان بررسی می‌شود.
# ============================================================

BLOCK_KEYWORDS = [

    # Shopping
    "buying guide",
    "price comparison",
    "best phones",
    "best phone",
    "best laptops",
    "best laptop",
    "budget phones",
    "budget phone",
    "budget laptops",
    "budget laptop",
    "phone deals",
    "laptop deals",
    "smartphone deals",
    "pricing",

    # Events / promotion
    "conference",
    "conference tickets",
    "event",
    "events",
    "summit",
    "disrupt",
    "side event",
    "ticket",
    "tickets",
    "webinar",
    "newsletter",
    "podcast",
    "advertisement",
    "sponsored",

    # Archive / navigation
    "archive",
    "archives",
    "download archive",
]


# ============================================================
# Normalize
# ============================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"[_/|]+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# Exact keyword matching
# ============================================================

def keyword_matches(
    text: str,
    keyword: str
) -> bool:

    text = normalize_text(text)
    keyword = normalize_text(keyword)

    if not text or not keyword:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(keyword)
        + r"(?![a-z0-9])"
    )

    return (
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )
        is not None
    )


# ============================================================
# English detection
# ============================================================

def is_english_text(text: str) -> bool:

    if not text:
        return False

    latin_chars = 0
    persian_chars = 0

    for char in str(text):

        if "a" <= char.lower() <= "z":
            latin_chars += 1

        elif "\u0600" <= char <= "\u06FF":
            persian_chars += 1

    if latin_chars < 20:
        return False

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

    return (
        english_ratio >= 0.85
        and persian_chars <= 20
    )


# ============================================================
# Technology relevance
# ============================================================

def is_technology_relevant(
    title: str,
    content: str
) -> bool:

    title = title or ""
    content = content or ""

    normalized_title = normalize_text(title)
    normalized_content = normalize_text(content)

    # --------------------------------------------------------
    # Language check
    # --------------------------------------------------------

    language_sample = (
        normalized_title
        + " "
        + normalized_content[:2500]
    )

    if not is_english_text(
        language_sample
    ):

        print(
            f"[FILTER NON-ENGLISH] {title}"
        )

        return False

    # --------------------------------------------------------
    # Block title
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Strong keyword in title
    # --------------------------------------------------------

    for keyword in STRONG_KEYWORDS:

        if keyword_matches(
            normalized_title,
            keyword
        ):

            print(
                f"[FILTER STRONG TITLE] "
                f"{keyword} -> {title}"
            )

            return True

    # --------------------------------------------------------
    # Strong keyword in content
    # --------------------------------------------------------

    strong_matches = []

    for keyword in STRONG_KEYWORDS:

        if keyword_matches(
            normalized_content,
            keyword
        ):

            strong_matches.append(
                keyword
            )

    # یک strong keyword در متن معمولاً کافی است،
    # چون این‌ها مشخصاً فناوری هستند.
    if strong_matches:

        print(
            f"[FILTER STRONG CONTENT] "
            f"{strong_matches[0]} -> {title}"
        )

        return True

    # --------------------------------------------------------
    # Medium keyword detection
    #
    # duplicate concepts مثل startup/startups
    # فقط یک match حساب می‌شوند.
    # --------------------------------------------------------

    medium_matches = set()

    for keyword in MEDIUM_KEYWORDS:

        if (
            keyword_matches(
                normalized_title,
                keyword
            )
            or
            keyword_matches(
                normalized_content,
                keyword
            )
        ):

            normalized_keyword = keyword

            # گروه‌بندی ساده
            if normalized_keyword in {
                "startup",
                "startups",
            }:
                normalized_keyword = "startup"

            elif normalized_keyword in {
                "robot",
                "robots",
            }:
                normalized_keyword = "robot"

            elif normalized_keyword in {
                "drone",
                "drones",
            }:
                normalized_keyword = "drone"

            medium_matches.add(
                normalized_keyword
            )

    # --------------------------------------------------------
    # Business keywords
    # --------------------------------------------------------

    business_matches = set()

    for keyword in BUSINESS_KEYWORDS:

        if keyword_matches(
            normalized_title,
            keyword
        ):

            business_matches.add(
                keyword
            )

    # --------------------------------------------------------
    # قانون پذیرش medium
    #
    # business-only -> reject
    #
    # medium + business -> accept
    #
    # دو medium مستقل -> accept
    # --------------------------------------------------------

    if len(medium_matches) >= 2:

        matches = sorted(
            medium_matches
        )

        print(
            f"[FILTER MEDIUM MATCH] "
            f"{matches[:6]} -> {title}"
        )

        return True

    if (
        medium_matches
        and business_matches
    ):

        matches = (
            sorted(medium_matches)
            + sorted(business_matches)
        )

        print(
            f"[FILTER MEDIUM + BUSINESS] "
            f"{matches[:6]} -> {title}"
        )

        return True

    # --------------------------------------------------------
    # هیچ تطابق قابل‌اعتماد
    # --------------------------------------------------------

    print(
        f"[FILTER NO MATCH] {title}"
    )

    return False
