import sqlite3
import datetime

from config import DB_NAME, TEST_MODE


# ============================================================
# اتصال به دیتابیس
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ============================================================
# راه‌اندازی دیتابیس
# ============================================================

def init_db() -> None:
    """
    راه‌اندازی اولیه دیتابیس و جدول‌های مورد نیاز ربات.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # اخبار پردازش‌شده
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # تنظیمات سیستم
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # --------------------------------------------------------
    # آمار روزانه
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            date TEXT PRIMARY KEY,
            articles_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0
        )
    """)

    # --------------------------------------------------------
    # ادمین‌های تایید شده
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authenticated_admins (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # --------------------------------------------------------
    # صف اخبار
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            url TEXT UNIQUE,

            title TEXT,

            content TEXT,

            image TEXT,

            source TEXT,

            status TEXT DEFAULT 'pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            processing_started_at TIMESTAMP,

            processed_at TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # تنظیمات پیش‌فرض
    # --------------------------------------------------------

    cursor.execute("""
        INSERT OR IGNORE INTO system_settings
        (key, value)
        VALUES ('bot_status', 'ON')
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO system_settings
        (key, value)
        VALUES ('bot_tone', 'official')
    """)

    # --------------------------------------------------------
    # حالت تست
    # --------------------------------------------------------

    if TEST_MODE:

        cursor.execute("""
            DELETE FROM processed_news
        """)

        cursor.execute("""
            DELETE FROM news_queue
        """)

        print(
            "[DATABASE] حالت تست فعال است: "
            "آرشیو و صف اخبار پاک شدند."
        )

    conn.commit()
    conn.close()


# ============================================================
# مدیریت ادمین
# ============================================================

def add_authenticated_admin(user_id: int) -> None:
    """
    اضافه کردن ادمین پس از ورود موفق.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO authenticated_admins (user_id)
        VALUES (?)
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def is_user_admin(user_id: int) -> bool:
    """
    بررسی تایید شدن کاربر به عنوان ادمین.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM authenticated_admins
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


# ============================================================
# آرشیو اخبار پردازش‌شده
# ============================================================

def manage_archive_limit() -> None:
    """
    نگه داشتن آخرین ۱۰ خبر در آرشیو processed_news.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM processed_news
    """)

    result = cursor.fetchone()

    count = result[0] if result else 0

    if count > 10:

        cursor.execute("""
            DELETE FROM processed_news
            WHERE id NOT IN (
                SELECT id
                FROM processed_news
                ORDER BY id DESC
                LIMIT 10
            )
        """)

        print(
            "[DATABASE] آرشیو اخبار به آخرین ۱۰ مورد محدود شد."
        )

    conn.commit()
    conn.close()


def is_url_processed(url: str) -> bool:
    """
    بررسی اینکه URL قبلاً پردازش شده است یا خیر.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM processed_news
        WHERE url = ?
        """,
        (url,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def mark_url_as_processed(
    url: str,
    title: str
) -> None:
    """
    ثبت خبر پردازش‌شده.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO processed_news
            (url, title)
            VALUES (?, ?)
            """,
            (url, title)
        )

        conn.commit()

    except sqlite3.IntegrityError:

        pass

    conn.close()

    manage_archive_limit()


# ============================================================
# تنظیمات سیستم
# ============================================================

def get_setting(key: str) -> str:
    """
    دریافت تنظیمات سیستم.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT value
        FROM system_settings
        WHERE key = ?
        """,
        (key,)
    )

    result = cursor.fetchone()

    conn.close()

    return result[0] if result else "ON"


def update_setting(
    key: str,
    value: str
) -> None:
    """
    بروزرسانی تنظیمات سیستم.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO system_settings
        (key, value)
        VALUES (?, ?)
        """,
        (key, value)
    )

    conn.commit()
    conn.close()


# ============================================================
# آمار روزانه
# ============================================================

def update_stats(tokens: int) -> None:
    """
    ثبت تعداد توکن‌های مصرف‌شده و اخبار پردازش‌شده امروز.
    """

    today = str(datetime.date.today())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO system_stats
        (date, articles_count, tokens_used)
        VALUES (?, 0, 0)
        """,
        (today,)
    )

    cursor.execute(
        """
        UPDATE system_stats

        SET
            articles_count = articles_count + 1,
            tokens_used = tokens_used + ?

        WHERE date = ?
        """,
        (tokens, today)
    )

    conn.commit()
    conn.close()


def get_today_stats() -> tuple:
    """
    دریافت آمار امروز.
    """

    today = str(datetime.date.today())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT articles_count, tokens_used
        FROM system_stats
        WHERE date = ?
        """,
        (today,)
    )

    result = cursor.fetchone()

    conn.close()

    return result if result else (0, 0)


# ============================================================
# صف اخبار
# ============================================================

def add_news_to_queue(
    url,
    title,
    content,
    image,
    source
):
    """
    اضافه کردن خبر جدید به صف.

    اگر URL قبلاً در صف وجود داشته باشد،
    خبر دوباره اضافه نمی‌شود.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO news_queue
        (
            url,
            title,
            content,
            image,
            source,
            status
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            'pending'
        )
        """,
        (
            url,
            title,
            content,
            image,
            source
        )
    )

    conn.commit()
    conn.close()


def get_pending_news(limit=None):
    """
    دریافت اخبار منتظر پردازش.

    اخبار بر اساس زمان ورود
    از قدیمی‌ترین به جدیدترین خوانده می‌شوند.
    """

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            url,
            title,
            content,
            image,
            source

        FROM news_queue

        WHERE status = 'pending'

        ORDER BY id ASC
    """

    params = ()

    if limit is not None:

        query += " LIMIT ?"

        params = (limit,)

    cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    return rows


# ============================================================
# شروع پردازش خبر
# ============================================================

def mark_news_processing(news_id):
    """
    خبر را وارد حالت processing می‌کند.

    نکته مهم:
    processing_started_at زمان شروع مصرف سهمیه AI است.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE news_queue

        SET
            status = 'processing',
            processing_started_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (news_id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# تکمیل پردازش
# ============================================================

def mark_news_completed(news_id):
    """
    ثبت موفقیت پردازش خبر.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE news_queue

        SET
            status = 'completed',
            processed_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (news_id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# بازگرداندن خبر به صف
# ============================================================

def mark_news_pending(news_id):
    """
    در صورت خطای موقت، خبر دوباره pending می‌شود.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE news_queue

        SET
            status = 'pending',
            processing_started_at = NULL

        WHERE id = ?
        """,
        (news_id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# تعداد درخواست‌های AI در یک ساعت اخیر
# ============================================================

def get_hourly_ai_usage():
    """
    تعداد درخواست‌های Gemini در یک ساعت اخیر.

    processing:
        از processing_started_at استفاده می‌شود.

    completed:
        از processed_at استفاده می‌شود.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)

        FROM news_queue

        WHERE

        (
            status = 'processing'
            AND processing_started_at >= datetime('now', '-1 hour')
        )

        OR

        (
            status = 'completed'
            AND processed_at >= datetime('now', '-1 hour')
        )
    """)

    result = cursor.fetchone()

    conn.close()

    return result[0] if result else 0


# ============================================================
# بررسی سهمیه AI
# ============================================================

def can_use_ai_hourly_limit(
    limit: int = 10
) -> bool:
    """
    بررسی می‌کند آیا هنوز سهمیه Gemini
    در یک ساعت اخیر باقی مانده است یا خیر.
    """

    usage = get_hourly_ai_usage()

    if usage >= limit:

        print(
            f"[AI LIMIT] سهمیه ساعتی پر شده است: "
            f"{usage}/{limit}"
        )

        return False

    print(
        f"[AI LIMIT] سهمیه موجود است: "
        f"{usage}/{limit}"
    )

    return True


# ============================================================
# دریافت وضعیت سهمیه AI
# ============================================================

def get_ai_hourly_status(
    limit: int = 10
):
    """
    برگرداندن وضعیت کامل سهمیه AI.
    """

    usage = get_hourly_ai_usage()

    remaining = max(
        0,
        limit - usage
    )

    return {
        "used": usage,
        "limit": limit,
        "remaining": remaining
    }

def get_completed_news(limit=10):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            source,
            status,
            processed_at
        FROM news_queue
        WHERE status = 'completed'
        ORDER BY processed_at DESC, id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows
