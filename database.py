import sqlite3
from config import DB_NAME

def init_db() -> None:
    """ساخت جدول دیتابیس در صورتی که از قبل وجود نداشته باشد"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_url_processed(url: str) -> bool:
    """بررسی تکراری نبودن لینک خبر"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_news WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_url_as_processed(url: str, title: str) -> None:
    """ذخیره لینک خبر پردازش شده در دیتابیس"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processed_news (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # لینک از قبل موجود است
    conn.close()
