# 🤖 Automated AI News Aggregator & Summarizer with Telegram Admin Panel

[EN] This project is an enterprise-grade automated tech news aggregator powered by Gemini / OpenAI API. It features a fully responsive Telegram Admin Control Panel, dynamic model tuning, automated DB flushing, and modular architecture optimized for production.

[FA] این پروژه یک سامانه پیشرفته و سطح تجاری برای جمع‌آوری و خلاصه‌سازی خودکار اخبار تکنولوژی با استفاده از هوش مصنوعی (Gemini/OpenAI) است. این پروژه مجهز به پنل کنترل ادمین در تلگرام، تغییر داینامیک لحن، چرخه هوشمند پاک‌سازی دیتابیس و معماری کاملاً ماژولار است.

---

## 🇬🇧 English Guide

### 📌 Key Features & Capabilities
* **Telegram Admin Control Panel**: Fully managed inside Telegram with interactive inline buttons (ON/OFF switch, dynamic AI tone selector, live scraper manual trigger, and resource usage reporting).
* **Breaking News System (🚨 Urgent)**: Admin receives a draft preview of the news and can broadcast it normally or tag it as *Breaking News* which triggers auto-pinning in the public channel.
* **Smart Archive Management**: Implements a rolling database engine that tracks the latest logs. Once the 11th article enters, it automatically purges the 10 oldest rows to keep server disk space minimal.
* **Text Chunking & HTML Formatting**: Automatically strips broken syntax marks and splits extra-long articles (over 4000 characters) into safe chunks to prevent Telegram API crashes.
* **Flexible AI Core**: Ready to process via Gemini 2.5 Flash natively, and architecturally wired to swap to OpenAI (`gpt-4o-mini`) seamlessly.
* **Developer Test Mode**: Includes a `TEST_MODE` configuration to auto-flush news cycles locally for debugging without requiring manual DB deletes.

### 📂 Modular Structure
* `config.py`: Main ecosystem variables, API keys, telegram tokens, and custom prompt configurations.
* `database.py`: Core SQLite layer executing tables initialization, usage statistics logging, and rolling archive purges.
* `ai_engine.py`: Dynamic context processing engine utilizing official AI SDKs.
* `scrapers/techcrunch.py`: Highly reliable semantic structural scraper built with explicit browser header impersonation.
* `main.py`: Central non-blocking asynchronous conductor hosting the `python-telegram-bot` thread and `BackgroundScheduler`.

### 🛠️ Local Development & Deployment (Windows)
1. Ensure Python 3.10+ is available. Activate your local virtual environment:
   ```bash
   pip install google-genai openai python-telegram-bot apscheduler requests beautifulsoup4
   ```
2. Open `config.py` and populate your `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`, and `ADMIN_TELEGRAM_ID`.
3. Set `TEST_MODE = True` for debugging.
4. Execute the system:
   ```bash
   python main.py
   ```

---

## 🇮🇷 راهنمای فارسی

### 📌 قابلیت‌های کلیدی و هوشمند سامانه
* **پنل مدیریت اختصاصی تلگرام**: کنترل کامل ربات از داخل تلگرام با دکمه‌های شیشه‌ای (خاموش/روشن کردن کل چرخه، تغییر لحظه‌ای لحن هوش مصنوعی، دکمه اجرای دستی اسکرپر و گزارش‌گیری زنده از آمار مصرف توکن‌ها).
* **سیستم تایید خبر فوری (Breaking News)**: ربات ابتدا پیش‌نویس خبر ترجمه‌شده را به چت شخصی ادمین می‌فرستد. ادمین می‌تواند خبر را به صورت عادی ارسال کند، آن را حذف کند، و یا با برچسب **🚨 فوری** به کانال شلیک کرده و خودکار پین کند.
* **مدیریت هوشمند دیتابیس (چرخه ۱۰ تایی)**: دیتابیس به صورت خودکار تعداد اخبار ذخیره شده را مانیتور می‌کند. به محض ورود ۱۱امین خبر، ۱۰ خبر قدیمی‌تر را کاملاً پاک (Flush) می‌کند تا فضای هارد سرور اوبونتو همیشه سبک بماند.
* **سیستم تکه‌تکه کردن متون طولانی**: در صورت اسکرپ شدن صفحات حجیم، سیستم متن را به بخش‌های مجاز تلگرام (زیر ۳۸۰۰ کاراکتر) خرد می‌کند و تگ‌های نامنظم HTML را اصلاح می‌کند تا از کرش ربات جلوگیری شود.
* **حالت تست اختصاصی**: تعبیه متغیر `TEST_MODE` در تنظیمات که به شما اجازه می‌دهد بدون نیاز به حذف دستی فایل دیتابیس، در هر بار اجرای پروژه روی ویندوز، لیست اخبار را سفید کنید تا راحت تست بگیرید.

### 📂 چیدمان ماژولار فایل‌ها
* `config.py`: مدیریت توکن‌ها، کلیدهای دسترسی هوش مصنوعی، تنظیمات کانال و پرامپت‌های داینامیک رسمی/صمیمی.
* `database.py`: مدیریت دیتابیس سبک SQLite، ثبت جداول آمار مصرف روزانه و چرخه حیات آرشیو اخبار.
* `ai_engine.py`: موتور پردازش محتوا منطبق بر کیت توسعه رسمی شرکت‌های گوگل و OpenAI.
* `scrapers/techcrunch.py`: اسکرپر بهینه‌سازی شده با هدرهای شبیه‌ساز مروگر برای دور زدن لایه‌های امنیتی سایت‌ها.
* `main.py`: هسته اصلی و هماهنگ‌کننده ربات که لوپ ناهمگام (Asyncio) و سیستم زمان‌بندی ۲ ساعته را مدیریت می‌کند.

### 🛠️ نحوه راه‌اندازی و تست روی ویندوز
۱. ترمینال ادیتور خود را باز کرده (محیط `.venv` فعال باشد) و پکیج‌ها را نصب کنید:
   ```bash
   pip install google-genai openai python-telegram-bot apscheduler requests beautifulsoup4
   ```
۲. فایل `config.py` را باز کرده و توکن ربات فادر، آیدی کانال و آیدی عددی تلگرام خود را جایگذاری کنید.
۳. متغیر `TEST_MODE` را روی حالت `True` بگذارید تا برای تست نیازی به حذف دستی دیتابیس نباشد.
۴. ربات را استارت کنید:
   ```bash
   python main.py
   ```
   *نکته: قبل از انتقال به سرور اوبونتو، حتماً `TEST_MODE` را روی `False` تنظیم کنید.*
