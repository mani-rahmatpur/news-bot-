import html
import re

import requests

from bs4 import BeautifulSoup

from typing import List, Dict

from database import is_url_processed


# ============================================================
# VentureBeat RSS
# ============================================================

FEEDS = [
    "https://venturebeat.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/rss+xml, "
        "application/xml, "
        "text/xml, "
        "text/html;q=0.9, "
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# Normalize HTML
# ============================================================

def _clean_rss_content(
    raw_content: str
) -> str:

    if not raw_content:
        return ""

    # Decode HTML entities
    content = html.unescape(
        raw_content
    )

    soup = BeautifulSoup(
        content,
        "html.parser"
    )

    # Remove unwanted elements
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "noscript",
        ]
    ):
        tag.decompose()

    text = " ".join(
        soup.stripped_strings
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text[:7000]


# ============================================================
# Extract image from RSS item
# ============================================================

def _extract_image(
    item
) -> str:

    # --------------------------------------------------------
    # media:content
    # --------------------------------------------------------

    media_content = item.find(
        "media:content"
    )

    if media_content:

        url = (
            media_content.get("url")
            or ""
        )

        if url:
            return url.strip()

    # --------------------------------------------------------
    # media:thumbnail
    # --------------------------------------------------------

    thumbnail = item.find(
        "media:thumbnail"
    )

    if thumbnail:

        url = (
            thumbnail.get("url")
            or ""
        )

        if url:
            return url.strip()

    # --------------------------------------------------------
    # enclosure
    # --------------------------------------------------------

    enclosure = item.find(
        "enclosure"
    )

    if enclosure:

        url = (
            enclosure.get("url")
            or ""
        )

        if url:
            return url.strip()

    # --------------------------------------------------------
    # image inside description
    # --------------------------------------------------------

    description = item.find(
        "description"
    )

    if description:

        raw = str(
            description
        )

        soup = BeautifulSoup(
            raw,
            "html.parser"
        )

        image = soup.find(
            "img"
        )

        if image:

            url = (
                image.get("src")
                or ""
            )

            if url:
                return url.strip()

    return ""


# ============================================================
# Extract URL
# ============================================================

def _extract_url(
    item
) -> str:

    # RSS link
    link = item.find(
        "link"
    )

    if link:

        href = (
            link.get("href")
            or link.get_text(
                strip=True
            )
            or ""
        )

        if href:
            return href.strip()

    # Atom link
    for link_tag in item.find_all(
        "link"
    ):

        href = (
            link_tag.get("href")
            or ""
        )

        if href:
            return href.strip()

    return ""


# ============================================================
# Extract content from RSS
# ============================================================

def _extract_content(
    item
) -> str:

    # --------------------------------------------------------
    # content:encoded
    # --------------------------------------------------------

    encoded = item.find(
        "content:encoded"
    )

    if encoded:

        content = _clean_rss_content(
            encoded.get_text()
        )

        if len(content) >= 300:
            return content

    # --------------------------------------------------------
    # description
    # --------------------------------------------------------

    description = item.find(
        "description"
    )

    if description:

        content = _clean_rss_content(
            description.decode_contents()
        )

        if len(content) >= 300:
            return content

    # --------------------------------------------------------
    # summary
    # --------------------------------------------------------

    summary = item.find(
        "summary"
    )

    if summary:

        content = _clean_rss_content(
            summary.decode_contents()
        )

        if len(content) >= 300:
            return content

    return ""


# ============================================================
# Scraper
# ============================================================

def scrape_venturebeat(
    max_articles: int = 5
) -> List[Dict[str, str]]:

    articles = []

    seen_urls = set()

    for feed_url in FEEDS:

        if len(articles) >= max_articles:
            break

        try:

            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.content,
                "xml"
            )

            items = soup.find_all(
                ["item", "entry"]
            )

            print(
                f"[SCRAPER] VentureBeat feed -> "
                f"{feed_url} -> "
                f"{len(items)} item(s)"
            )

            for item in items:

                if len(articles) >= max_articles:
                    break

                # ------------------------------------------------
                # URL
                # ------------------------------------------------

                url = _extract_url(
                    item
                )

                if not url:
                    continue

                if (
                    "venturebeat.com"
                    not in url.lower()
                ):
                    continue

                # ------------------------------------------------
                # Ignore non-news areas
                # ------------------------------------------------

                blocked_paths = [
                    "/deals/",
                    "/events/",
                    "/vbtransform",
                    "/category/",
                    "/tag/",
                    "/author/",
                    "/resources/",
                ]

                if any(
                    path in url.lower()
                    for path in blocked_paths
                ):
                    continue

                # ------------------------------------------------
                # Duplicate URL
                # ------------------------------------------------

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                # ------------------------------------------------
                # Already processed
                # ------------------------------------------------

                if is_url_processed(
                    url
                ):

                    print(
                        f"[VB SKIPPED] "
                        f"Already processed: {url}"
                    )

                    continue

                # ------------------------------------------------
                # Title
                # ------------------------------------------------

                title_tag = item.find(
                    "title"
                )

                title = ""

                if title_tag:

                    title = title_tag.get_text(
                        " ",
                        strip=True
                    )

                if not title:
                    continue

                # ------------------------------------------------
                # Content
                # ------------------------------------------------

                content = _extract_content(
                    item
                )

                if len(content) < 300:

                    print(
                        f"[VB CONTENT TOO SHORT] "
                        f"{title}"
                    )

                    continue

                # ------------------------------------------------
                # Image
                # ------------------------------------------------

                image = _extract_image(
                    item
                )

                # ------------------------------------------------
                # Store
                # ------------------------------------------------

                articles.append(
                    {
                        "url": url,
                        "title": title,
                        "content": content,
                        "image": image,
                        "source": "VentureBeat",
                    }
                )

        except Exception as feed_error:

            print(
                f"[VB FEED ERROR] "
                f"{feed_url}: {feed_error}"
            )

    print(
        f"[SCRAPER] VentureBeat -> "
        f"{len(articles)} article(s)"
    )

    return articles
