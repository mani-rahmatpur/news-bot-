# 🤖 AI Tech News Telegram Bot

ربات هوشمند جمع‌آوری و انتشار اخبار تکنولوژی، هوش مصنوعی و ارزهای دیجیتال در تلگرام.

این پروژه به‌صورت خودکار اخبار را از منابع معتبر فناوری جمع‌آوری کرده، محتوای آن‌ها را پردازش می‌کند، اخبار غیرمرتبط را فیلتر می‌کند و پس از بازنویسی با هوش مصنوعی در کانال تلگرام منتشر می‌کند.

---

## ✨ Features

* جمع‌آوری اخبار از:

  * Zoomit
  * Digiato
  * TechCrunch

* فیلتر هوشمند اخبار

  * هوش مصنوعی (AI)
  * رمزارزها (Crypto)
  * بلاکچین
  * Web3
  * ChatGPT
  * Gemini
  * OpenAI
  * Claude
  * Grok

* حذف خودکار اخبار غیرمرتبط:

  * گوشی موبایل
  * لپ‌تاپ
  * راهنمای خرید
  * بررسی قیمت
  * ساعت هوشمند
  * هدفون
  * محصولات مصرفی

* بازنویسی اخبار با هوش مصنوعی

* تولید تصویر برای خبرها

* ارسال پیش‌نمایش برای مدیر

* انتشار خودکار در کانال تلگرام

* جلوگیری از انتشار خبرهای تکراری

---

## 🏗 Project Structure

```text
telegrambot/
│
├── main.py
├── ai_engine.py
├── filters.py
├── database.py
├── config.py
│
├── scrapers/
│   ├── zoomit.py
│   ├── digiato.py
│   └── techcrunch.py
│
├── news.db
└── requirements.txt
```

---

## ⚙ Requirements

* Python 3.12+
* Telegram Bot Token
* Telegram Channel ID
* Gemini API Key

---

## 🚀 Installation

Clone repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

cd YOUR_REPOSITORY
```

Create virtual environment:

```bash
python3 -m venv venv

source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration

Create `config.py`

```python
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"

TELEGRAM_CHANNEL_ID = "@your_channel"

ADMIN_TELEGRAM_ID = 123456789

ADMIN_PASSWORD = "password"

GEMINI_API_KEY = "YOUR_API_KEY"
```

---

## ▶ Running

```bash
python3 main.py
```

Or with PM2:

```bash
pm2 start main.py \
--name telegrambot \
--interpreter ./venv/bin/python
```

Restart:

```bash
pm2 restart telegrambot
```

Logs:

```bash
pm2 logs telegrambot
```

---

## 🧠 Filtering Logic

The bot only accepts news related to:

* Artificial Intelligence
* Machine Learning
* LLMs
* Crypto
* Blockchain
* Web3
* OpenAI
* Gemini
* ChatGPT
* Claude
* Grok

Examples of filtered content:

* Smartphone launches
* Laptop reviews
* Buying guides
* Price comparison articles
* Consumer electronics promotions

---

## 📡 Workflow

```text
Scrapers
    ↓
News Collection
    ↓
Duplicate Check
    ↓
Technology Filter
    ↓
AI Rewrite
    ↓
Image Generation
    ↓
Admin Preview
    ↓
Telegram Channel
```

---

## 🛡 Anti-Duplicate System

تمام URLهای پردازش‌شده در پایگاه داده ذخیره می‌شوند تا از انتشار مجدد خبرها جلوگیری شود.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Developed for automated AI, Crypto and Technology news publishing on Telegram.
