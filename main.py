from typing import List, Dict
from database import init_db, mark_url_as_processed
from ai_engine import process_news_with_ai
from scrapers.techcrunch import scrape_techcrunch


def main() -> None:
    # ۱. آماده‌سازی دیتابیس
    init_db()
    print("Checking for new technology updates...")

    # ۲. جمع‌آوری اخبار جدید از اسکرپرها
    new_articles: List[Dict[str, str]] = []
    new_articles.extend(scrape_techcrunch())

    if not new_articles:
        print("No new articles found since the last run.")
        return

    # ۳. پردازش اخبار تک به تک توسط هوش مصنوعی
    for article in new_articles:
        print(f"\nProcessing: {article['title']}")

        # ارسال متن به موتور OpenAI
        ai_output = process_news_with_ai(article["content"])

        if ai_output:
            print("--- AI Generated Output ---")
            print(ai_output)
            print("----------------------------")

            # ذخیره در دیتابیس برای جلوگیری از پردازش مجدد در اجرای بعدی
            mark_url_as_processed(article["url"], article["title"])


if __name__ == "__main__":
    main()
