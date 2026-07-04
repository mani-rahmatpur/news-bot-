# 🤖 Automated AI News Aggregator & Summarizer

[EN] This project is an automated tech news aggregator and summarizer powered by the OpenAI API. It features a modular, production-ready architecture optimized for both Windows testing and Ubuntu server deployment.

[FA] این پروژه یک ربات خودکار جمع‌آوری، فیلتر و خلاصه‌سازی اخبار تکنولوژی با استفاده از هوش مصنوعی (OpenAI API) است که با معماری چندفایلی و بهینه برای سیستم‌عامل‌های ویندوز و اوبونتو طراحی شده است.

---

## 🇬🇧 English Guide

### 📌 Project Structure
* `config.py`: Manages API keys, database paths, and custom AI prompt configurations.
* `database.py`: Handles the SQLite database to store links and prevent parsing duplicate news.
* `ai_engine.py`: The core engine communicating with the OpenAI API (optimized for `gpt-4o-mini`).
* `scrapers/`: A modular folder dedicated to housing independent web scrapers (currently features TechCrunch).
* `main.py`: The central orchestrator that coordinates and triggers all operations.

### 🛠️ Installation & Setup (Windows Testing)
1. Ensure Python 3.10 or higher is installed on your machine.
2. Open your IDE terminal and install the required dependencies:
   ```bash
   pip install requests beautifulsoup4 openai
   ```
3. Set your OpenAI API Key as an environment variable (Windows CMD):
   ```cmd
   set OPENAI_API_KEY=your_actual_api_key_here
   ```
4. Run the robot:
   ```bash
   python main.py
   ```

### 🚀 Production Deployment Notes (Ubuntu Server)
* **Do not** copy local configuration folders such as `.idea`, `.venv`, and `__pycache__` to the server.
* Transfer only the core Python source files and the `scrapers/` folder.
* Recreate a fresh virtual environment natively on Ubuntu, install dependencies, and configure a Cron Job using `crontab -e` to schedule regular automated intervals.

---

## 🇮🇷 راهنمای فارسی

### 📌 ساختار پروژه
* `config.py`: مدیریت کلیدهای دسترسی، تنظیمات دیتابیس و پرامپت اختصاصی هوش مصنوعی.
* `database.py`: مدیریت دیتابیس SQLite برای ذخیره لینک‌ها و جلوگیری از پردازش اخبار تکراری.
* `ai_engine.py`: موتور ارتباط با API هوش مصنوعی (مدل `gpt-4o-mini`).
* `scrapers/`: پوشه ماژولار برای قرارگیری اسکرپرهای سایت‌های مختلف (در حال حاضر شامل TechCrunch).
* `main.py`: هسته اصلی ربات که تمام اجزا را هماهنگ و اجرا می‌کند.

### 🛠️ نیازمندی‌ها و راه‌اندازی روی ویندوز
۱. مطمئن شوید که پایتون نسخه ۳.۱۰ یا بالاتر روی سیستم نصب است.
۲. ترمینال ادیتور خود را باز کرده و پکیج‌های مورد نیاز را نصب کنید:
   ```bash
   pip install requests beautifulsoup4 openai
   ```
۳. کلید API خود را به عنوان متغیر سیستم تعریف کنید (در CMD ویندوز):
   ```cmd
   set OPENAI_API_KEY=your_actual_api_key_here
   ```
۴. ربات را اجرا کنید:
   ```bash
   python main.py
   ```

### 🚀 نحوه انتقال به سرور اوبونتو (Ubuntu Server)
* پوشه‌های `.idea`، `.venv` و `__pycache__` را کپی نکنید.
* فقط فایل‌های اصلی پایتون و پوشه `scrapers` را به سرور منتقل کنید.
* یک محیط مجازی جدید روی سرور بسازید، پکیج‌ها را نصب کنید و یک Cron Job با دستور `crontab -e` برای اجرای خودکار (مثلاً هر ۲ ساعت) تنظیم کنید.
