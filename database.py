import sqlite3
from config import DB_NAME, TEST_MODE


def init_db() -> None:
    """راه‌اندازی اولیه دیتابیس و جدول‌های مورد نیاز سیستم ادمین"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # جدول ذخیره اخبار پردازش شده جهت جلوگیری از ارسال تکراری
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # جدول ذخیره وضعیت دکمه‌های روشن/خاموش و لحن پنل ادمین
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # جدول ثبت تعداد اخبار ارسالی و توکن‌های مصرفی روزانه جهت آمار پنل
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_stats (
            date TEXT PRIMARY KEY,
            articles_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0
        )
    ''')
    # جدول ذخیره آیدی عددی ادمین‌های تایید شده با رمز عبور
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authenticated_admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    # ثبت تنظیمات پیش‌فرض پنل در اولین اجرای ربات
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('bot_status', 'ON')")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('bot_tone', 'official')")

    # منطق حالت تست: در صورت روشن بودن، جدول اخبار را خالی کن تا بدون وقفه تست کنی
    if TEST_MODE:
        cursor.execute("DELETE FROM processed_news")
        print("[DATABASE] حالت تست فعال است: لیست اخبار آرشیو به صورت خودکار خالی شد.")

    conn.commit()
    conn.close()


def add_authenticated_admin(user_id: int) -> None:
    """اضافه کردن یک ادمین جدید به لیست تایید شده‌ها پس از وارد کردن رمز صحیح"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO authenticated_admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def is_user_admin(user_id: int) -> bool:
    """بررسی اینکه آیا کاربر ادمین تایید شده است یا خیر"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM authenticated_admins WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None


def manage_archive_limit() -> None:
    """منطق آرشیو ۱۰ تایی: اگر اخبار از ۱۰ بیشتر شد، قدیمی‌ها را پاک کن تا دیتابیس سبک بماند"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processed_news")
    res = cursor.fetchone()
    count = res[0] if res else 0

    if count > 10:
        cursor.execute("SELECT id FROM processed_news ORDER BY id DESC LIMIT 1")
        res_last = cursor.fetchone()
        last_id = res_last[0] if res_last else None
        if last_id:
            cursor.execute("DELETE FROM processed_news WHERE id < ?", (last_id,))
            print(f"[DATABASE] دیتابیس آرشیو پاک شد. چرخه جدید با خبر آی‌دی {last_id} آغاز گشت.")
    conn.commit()
    conn.close()


def is_url_processed(url: str) -> bool:
    """بررسی اینکه آیا این لینک خبر قبلاً توسط ربات پردازش شده است یا خیر"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_news WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_url_as_processed(url: str, title: str) -> None:
    """ذخیره لینک خبر ارسال شده در دیتابیس و اجرای چک‌لیست آرشیو ۱۰ تایی"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processed_news (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    manage_archive_limit()


def get_setting(key: str) -> str:
    """دریافت مقادیر تنظیمات پنل (مثل روشن یا خاموش بودن ربات) از دیتابیس"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "ON"


def update_setting(key: str, value: str) -> None:
    """به‌روزرسانی تنظیمات پنل مدیریت ادمین در دیتابیس"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def update_stats(tokens: int) -> None:
    """ثبت و آپدیت آمار توکن‌های مصرفی و تعداد اخبار امروز"""
    import datetime
    today = str(datetime.date.today())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO system_stats (date) VALUES (?)", (today,))
    cursor.execute(
        "UPDATE system_stats SET articles_count = articles_count + 1, tokens_used = tokens_used + ? WHERE date = ?",
        (tokens, today))
    conn.commit()
    conn.close()


def get_today_stats() -> tuple:
    """دریافت گزارش عملکرد امروز برای نمایش دکمه آمار در پنل تلگرام ادمین"""
    import datetime
    today = str(datetime.date.today())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT articles_count, tokens_used FROM system_stats WHERE date = ?", (today,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0)
