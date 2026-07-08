# 🤖 AI-Powered Telegram Tech News Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)]()
[![Gemini AI](https://img.shields.io/badge/Google-Gemini-orange.svg)]()
[![SQLite](https://img.shields.io/badge/Database-SQLite-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

An advanced AI-powered Telegram News Aggregator that automatically collects, translates, rewrites, summarizes, reviews, and publishes technology news from multiple trusted sources.

The system is designed for production environments and includes a Telegram-based Admin Control Panel, AI-powered content processing, secure credential management, news approval workflows, automatic database maintenance, and intelligent error recovery.

---

# 🇬🇧 English Documentation

## 🚀 Features

### 📰 Multi-Source News Aggregation

The bot automatically collects news from:

- TechCrunch
- Zoomit
- Digiato

Additional sources can be added through the modular scraper architecture.

---

### 🤖 AI Content Processing

Powered by Google Gemini.

Capabilities:

- Translate English articles into Persian
- Rewrite Persian articles uniquely
- Generate attractive headlines
- Create structured summaries
- Extract key points
- Generate relevant hashtags
- Support multiple writing styles

---

### 🎭 Dynamic AI Tone System

Administrators can switch tone directly from Telegram:

#### Official

Professional journalism style.

#### Friendly

Casual and conversational style.

#### Funny

Humorous and sarcastic style.

No server restart required.

---

### 🔐 Secure Credential Management

Sensitive information is stored outside the source code.

Secrets are loaded from:

```text
telegrambot/secrets/bot.env
```

Contains:

```env
GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=
ADMIN_PASSWORD=
```

This prevents API keys and passwords from being exposed in Git repositories.

---

### 👨‍💼 Telegram Admin Panel

The entire system can be managed from Telegram.

Available controls:

- Bot ON/OFF
- Change AI Tone
- Manual News Processing
- Usage Statistics
- News Approval Workflow

---

### 📝 News Approval Workflow

Every generated article is first sent privately to the administrator.

The administrator can:

- ✅ Publish Normally
- 🔥 Publish as Breaking News
- ✏️ Edit Content
- ❌ Reject Article

This prevents unwanted content from being published automatically.

---

### 📊 Usage Statistics

Tracks:

- Processed articles
- Daily AI token usage
- Bot activity metrics

Statistics can be viewed directly from Telegram.

---

### 🗄️ Smart Database Management

SQLite is used as the storage engine.

Features:

- Processed news tracking
- Duplicate prevention
- Admin authentication
- Daily statistics
- Dynamic settings

---

### 🔄 Rolling Archive System

To keep the server lightweight:

- Old news entries are automatically purged
- Archive size is controlled automatically
- Database remains compact

---

### 🛡️ Crash Recovery System

The bot continues operating even if:

- Gemini API quota is exceeded
- Scrapers fail
- Image generation fails
- Telegram API returns errors
- Network interruptions occur

---

### 📷 Intelligent Media Handling

Supports:

- AI-generated images (when available)
- Fallback source images
- Safe media delivery
- Automatic text splitting for long messages

---

### ⚙️ Developer Test Mode

```python
TEST_MODE = True
```

Useful during development.

Automatically resets processed-news tracking so testing can be repeated without manually cleaning the database.

---

# 📂 Project Structure

```text
telegrambot/

├── main.py
├── ai_engine.py
├── config.py
├── database.py
├── news_database.db
│
├── scrapers/
│   ├── techcrunch.py
│   ├── zoomit.py
│   └── digiato.py
│
├── secrets/
│   └── bot.env
│
├── venv/
│
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/telegram-ai-news-bot.git

cd telegram-ai-news-bot
```

---

## Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install \
google-genai \
python-telegram-bot[job-queue] \
requests \
beautifulsoup4
```

---

# 🔐 Configure Secrets

Create:

```bash
mkdir secrets

nano secrets/bot.env
```

Example:

```env
GEMINI_API_KEY=YOUR_GEMINI_KEY

TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN

ADMIN_PASSWORD=YOUR_PASSWORD
```

---

# ⚙️ Configure Bot

Open:

```python
config.py
```

Set:

```python
TELEGRAM_CHANNEL_ID = "@yourchannel"

ADMIN_TELEGRAM_ID = 123456789
```

---

# ▶️ Run Locally

```bash
python main.py
```

---

# 🚀 Production Deployment (Ubuntu + PM2)

Install PM2:

```bash
npm install -g pm2
```

Start:

```bash
pm2 start main.py \
--name telegrambot \
--interpreter python3
```

View logs:

```bash
pm2 logs telegrambot
```

Restart:

```bash
pm2 restart telegrambot
```

Status:

```bash
pm2 status
```

Save startup configuration:

```bash
pm2 save
```

---

# 🗄️ Database Tables

### processed_news

Stores previously published news.

### authenticated_admins

Stores authenticated administrators.

### system_settings

Stores:

- bot_status
- bot_tone

### system_stats

Stores:

- daily processed articles
- token usage

---

# 🔄 News Processing Pipeline

```text
TechCrunch
      │
Zoomit
      │
Digiato
      ▼
   Scrapers
      ▼
 Gemini AI
      ▼
 Pending Queue
      ▼
 Admin Review
      ▼
 Telegram Channel
```

---

# 🧠 Current AI Models

### Content Generation

```text
Gemini 2.5 Flash
```

### Image Generation

Currently disabled due Gemini Free Tier limitations.

Fallback source images are used automatically.

---

# 📋 Future Roadmap

- Web Admin Dashboard
- Multi-channel Publishing
- Scheduled Publishing
- AI Image Generation Queue
- Automatic Categorization
- Cloud Storage
- OpenAI Support
- Claude Support
- DeepSeek Support
- Advanced Analytics Dashboard
- Multi-language Publishing

---

# 🇮🇷 مستندات فارسی

## 📌 معرفی پروژه

این پروژه یک ربات پیشرفته تلگرام برای جمع‌آوری، ترجمه، بازنویسی و انتشار اخبار فناوری است که با استفاده از هوش مصنوعی Gemini کار می‌کند.

تمام فرآیند از دریافت خبر تا تأیید نهایی و انتشار، از داخل تلگرام قابل مدیریت است.

---

## ✨ امکانات اصلی

### 📰 جمع‌آوری خودکار اخبار

پشتیبانی از:

- TechCrunch
- زومیت
- دیجیاتو

---

### 🤖 پردازش هوشمند اخبار

- ترجمه اخبار انگلیسی به فارسی
- بازنویسی کامل اخبار فارسی
- تولید تیتر جذاب
- خلاصه‌سازی هوشمند
- استخراج نکات مهم
- تولید هشتگ مرتبط

---

### 🎭 سه لحن مختلف

- رسمی (Official)
- دوستانه (Friendly)
- طنز (Funny)

قابل تغییر از داخل پنل تلگرام.

---

### 🔒 امنیت اطلاعات

کلیدها و رمزها داخل سورس ذخیره نمی‌شوند.

اطلاعات محرمانه از فایل:

```text
secrets/bot.env
```

خوانده می‌شوند.

---

### 👨‍💼 پنل مدیریت تلگرام

امکانات:

- روشن / خاموش کردن ربات
- تغییر لحن
- مشاهده آمار
- اجرای دستی اسکرپر
- مدیریت اخبار

---

### 📝 تأیید خبر قبل از انتشار

برای هر خبر:

- ارسال عادی
- ارسال فوری
- ویرایش
- حذف

---

### 📊 آمار روزانه

نمایش:

- تعداد اخبار
- مصرف توکن
- وضعیت عملکرد ربات

---

### 🛡️ سیستم بازیابی خطا

ربات در صورت بروز خطا متوقف نمی‌شود.

مدیریت:

- خطاهای Gemini
- خطاهای تلگرام
- خطاهای اسکرپر
- قطعی شبکه
- خطاهای ارسال تصویر

---

# 📄 License

MIT License

---

# 👨‍💻 Author

Developed for automated Persian technology news publishing using AI-powered workflows and Telegram administration.
