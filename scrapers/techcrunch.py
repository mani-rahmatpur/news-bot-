import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from database import is_url_processed

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_techcrunch() -> List[Dict[str, str]]:
    articles = []

    try:
        response = requests.get(
            "https://techcrunch.com",
            headers=HEADERS,
            timeout=20
        )

        soup = BeautifulSoup(response.text, "html.parser")

        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if (
                    href.startswith("https://techcrunch.com/")
                    and len(href) > 50
                    and "/video/" not in href
                    and "/podcast/" not in href
                    and "/author/" not in href
                    and "/tag/" not in href
                    and "/category/" not in href
                    and "/events/" not in href
                    and "#" not in href
            ):
                links.add(href)

        print(f"[SCRAPER] TechCrunch Links Found: {len(links)}")

        for article_url in list(links)[:5]:

            if is_url_processed(article_url):
                continue

            try:

                article_response = requests.get(
                    article_url,
                    headers=HEADERS,
                    timeout=20
                )

                article_soup = BeautifulSoup(
                    article_response.text,
                    "html.parser"
                )

                title = ""

                if article_soup.find("meta", property="og:title"):
                    title = article_soup.find(
                        "meta",
                        property="og:title"
                    ).get("content", "")

                if not title:
                    h1 = article_soup.find("h1")
                    title = h1.text.strip() if h1 else "TechCrunch Update"

                image = ""

                og_img = article_soup.find(
                    "meta",
                    property="og:image"
                )

                if og_img:
                    image = og_img.get("content", "")

                paragraphs = article_soup.find_all("p")

                content = " ".join(
                    p.get_text(" ", strip=True)
                    for p in paragraphs
                )

                if len(content) < 300:
                    continue

                articles.append({
                    "url": article_url,
                    "title": title,
                    "content": content[:6000],
                    "image": image,
                    "source": "TechCrunch"
                })

            except Exception as e:
                print(f"[ARTICLE ERROR] {e}")

    except Exception as e:
        print(f"[SCRAPER ERROR] TechCrunch: {e}")

    print(f"[SCRAPER] TechCrunch -> {len(articles)} article(s)")
    return articles
