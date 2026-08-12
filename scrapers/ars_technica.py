import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from database import is_url_processed


FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://arstechnica.com/ai/feed/",
    "https://arstechnica.com/security/feed/",
    "https://arstechnica.com/information-technology/feed/",
    "https://arstechnica.com/gadgets/feed/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


def _clean_html(value: str) -> str:
    if not value:
        return ""

    soup = BeautifulSoup(value, "html.parser")

    return " ".join(
        soup.stripped_strings
    )


def _get_article_content(
    url: str
) -> tuple[str, str]:

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # --------------------------------------------------------
    # تصویر اصلی
    # --------------------------------------------------------

    image_url = ""

    meta_image = soup.find(
        "meta",
        property="og:image"
    )

    if meta_image:
        image_url = (
            meta_image.get("content")
            or ""
        )

    # --------------------------------------------------------
    # پیدا کردن بدنه مقاله
    # --------------------------------------------------------

    article_root = soup.find("article")

    if article_root:
        paragraphs = article_root.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    content_parts = []

    for paragraph in paragraphs:

        text = paragraph.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        lowered = text.lower()

        # حذف متن‌های غیرمقاله
        if (
            "ars technica has been separating" in lowered
            or "separating the signal from the noise" in lowered
            or "you don't need to know everything" in lowered
            or "you don’t need to know everything" in lowered
        ):
            break

        content_parts.append(text)

    content = " ".join(
        content_parts
    ).strip()

    # --------------------------------------------------------
    # حذف هر footer باقی‌مانده در متن نهایی
    # --------------------------------------------------------

    footer_markers = [
        "ars technica has been separating",
        "separating the signal from the noise",
        "you don't need to know everything",
        "you don’t need to know everything",
    ]

    content_lower = content.lower()

    for marker in footer_markers:

        position = content_lower.find(
            marker
        )

        if position != -1:

            content = content[:position].strip()

            break

    # --------------------------------------------------------
    # محدود کردن طول
    # --------------------------------------------------------

    content = content[:7000]

    return content, image_url


def scrape_ars_technica(
    max_articles: int = 5
) -> List[Dict[str, str]]:

    """
    دریافت اخبار انگلیسی Ars Technica.

    منابع:
    - All News
    - AI
    - Security
    - Information Technology
    - Gadgets
    """

    articles = []

    seen_urls = set()

    for feed_url in FEEDS:

        if len(articles) >= max_articles:
            break

        try:

            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "xml"
            )

            items = soup.find_all(
                ["item", "entry"]
            )

            print(
                f"[SCRAPER] Ars Technica feed -> "
                f"{feed_url} -> {len(items)} item(s)"
            )

            for item in items:

                if len(articles) >= max_articles:
                    break

                # RSS
                link_tag = item.find("link")

                # بعضی feedها Atom هستند
                if link_tag:

                    url = (
                        link_tag.get("href")
                        or link_tag.get_text(
                            strip=True
                        )
                        or ""
                    )

                else:

                    url = ""

                title_tag = item.find("title")

                title = (
                    title_tag.get_text(
                        " ",
                        strip=True
                    )
                    if title_tag
                    else ""
                )

                if not url or not title:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                if is_url_processed(url):
                    continue

                try:

                    content, image_url = (
                        _get_article_content(url)
                    )

                except Exception as article_error:

                    print(
                        "[ARS ARTICLE ERROR] "
                        f"{article_error}"
                    )

                    continue

                if len(content.strip()) < 300:
                    continue

                articles.append(
                    {
                        "url": url,
                        "title": title,
                        "content": content[:6000],
                        "image": image_url,
                        "source": "Ars Technica",
                    }
                )

        except Exception as feed_error:

            print(
                "[ARS FEED ERROR] "
                f"{feed_url}: {feed_error}"
            )

    print(
        f"[SCRAPER] Ars Technica -> "
        f"{len(articles)} article(s)"
    )

    return articles
