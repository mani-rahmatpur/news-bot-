from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from database import is_url_processed


def scrape_techcrunch() -> List[Dict[str, str]]:
    """اسکرپ و استخراج ۵ خبر آخر سایت تک‌کرانچ"""
    url: str = "https://techcrunch.com"
    headers: Dict[str, str] = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    articles: List[Dict[str, str]] = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # پیدا کردن بلوک‌های اصلی خبر در قالب جدید سایت تک‌کرانچ
        for post in soup.find_all("div", class_="wp-block-post", limit=5):
            link_tag = post.find("a")
            if link_tag and link_tag.get("href"):
                article_url: str = str(link_tag["href"])
                article_title: str = link_tag.text.strip()

                # اگر این لینک قبلاً پردازش نشده بود، وارد متن خبر شو
                if not is_url_processed(article_url):
                    art_resp = requests.get(article_url, headers=headers, timeout=10)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")

                    # جمع‌آوری پاراگراف‌های اصلی متن خبر
                    paragraphs = art_soup.find_all("p")
                    full_text: str = " ".join([p.text for p in paragraphs])

                    articles.append({
                        "url": article_url,
                        "title": article_title,
                        "content": full_text[:4000]  # محدودیت ۴۰۰۰ کاراکتری برای مدیریت توکن و هزینه
                    })
    except Exception as e:
        print(f"Error scraping TechCrunch: {e}")

    return articles
