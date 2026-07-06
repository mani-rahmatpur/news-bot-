import sqlite3
from config import DB_NAME, TEST_MODE


def init_db() -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ساخت جدول‌ها در صورت عدم وجود
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_stats (
            date TEXT PRIMARY KEY,
            articles_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('bot_status', 'ON')")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('bot_tone', 'official')")

    # اصلاح هوشمندانه: به جای حذف فایل، جدول اخبار را خالی کن تا قفل ویندوز رخ ندهد
    if TEST_MODE:
        cursor.execute("DELETE FROM processed_news")
        print("[DATABASE] حالت تست فعال است: لیست اخبار آرشیو به صورت خودکار برای تست جدید خالی شد.")

    conn.commit()
    conn.close()


def manage_archive_limit() -> None:
    """منطق آرشیو ۱۰ تایی: اگر تعداد از ۱۰ بیشتر شد، دیتابیس ریست شده و فقط آخرین خبر می‌ماند"""
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
            print(f"[DATABASE] دیتابیس آرشیو با موفقیت پاک شد. چرخه جدید با خبر آی‌دی {last_id} آغاز گشت.")
    conn.commit()
    conn.close()


def is_url_processed(url: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_news WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_url_as_processed(url: str, title: str) -> None:
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "ON"


def update_setting(key: str, value: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def update_stats(tokens: int) -> None:
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
    import datetime
    today = str(datetime.date.today())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT articles_count, tokens_used FROM system_stats WHERE date = ?", (today,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0)
