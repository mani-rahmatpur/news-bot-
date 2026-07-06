from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from database import is_url_processed


def scrape_techcrunch() -> List[Dict[str, str]]:
    url: str = "https://techcrunch.com"
    headers: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles: List[Dict[str, str]] = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        links_found: List[str] = []

        for article_tag in soup.find_all("article"):
            link_tag = article_tag.find("a", href=True)
            if link_tag:
                href = str(link_tag["href"])
                if "://techcrunch.com" in href and href not in links_found:
                    links_found.append(href)

        if not links_found:
            for a_tag in soup.find_all("a", href=True):
                href = str(a_tag["href"])
                if "://techcrunch.com" in href and href not in links_found:
                    if "#comments" not in href:
                        links_found.append(href)

        for article_url in links_found[:3]:
            if not is_url_processed(article_url):
                art_resp = requests.get(article_url, headers=headers, timeout=15)
                art_soup = BeautifulSoup(art_resp.text, "html.parser")

                title_tag = art_soup.find("h1")
                article_title = title_tag.text.strip() if title_tag else "TechCrunch Update"

                paragraphs = art_soup.find_all("p")
                full_text: str = " ".join([p.text for p in paragraphs])

                if len(full_text.strip()) > 100:
                    articles.append({
                        "url": article_url,
                        "title": article_title,
                        "content": full_text[:4000]
                    })
    except Exception as e:
        print(f"Error scraping TechCrunch: {e}")

    return articles
