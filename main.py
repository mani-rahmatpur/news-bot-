import logging
import asyncio
import html
import re
import io
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database
from ai_engine import process_news_with_ai, generate_image_with_ai
# ایمپورت کردن اسکرپرهای ۳ وب‌سایت مرجع تکنولوژی
from scrapers.techcrunch import scrape_techcrunch
from scrapers.zoomit import scrape_zoomit
from scrapers.digiato import scrape_digiato
from filters import is_technology_relevant
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, ADMIN_TELEGRAM_ID, ADMIN_PASSWORD

# تنظیم لایه لاگ روی خطاهای بحرانی برای تمیز ماندن محیط ترمینال
logging.basicConfig(level=logging.ERROR)

pending_news = {}
user_editing_state = {}

diagnostic = {
    "techcrunch": 0,
    "zoomit": 0,
    "digiato": 0,
    "gemini": "OK",
    "image_ai": "OK",
    "telegram": "OK",
    "last_error": "-"
}


def clean_html_formatting(text: str) -> str:
    """پاک‌سازی متون هوش مصنوعی و هماهنگ کردن ستاره‌های مارک‌داون با تگ‌های امن HTML تلگرام"""
    text = html.escape(text)
    text = text.replace("&amp;", "&")
    pattern = re.compile(r'\*\*(.*?)\*\*')
    text = pattern.sub(r'<b>\1</b>', text)
    text = text.replace("<b></b>", "")
    return text

def generate_hashtags(text: str) -> str:
    """
    تولید هشتگ ساده از متن خبر
    """

    words = text.split()

    hashtags = []

    keywords = [
        "هوش_مصنوعی",
        "فناوری",
        "تکنولوژی",
        "گجت",
        "موبایل",
        "اینترنت",
        "گوگل",
        "اپل",
        "مایکروسافت",
        "ربات",
        "کامپیوتر",
        "امنیت"
    ]

    for word in keywords:
        if word.replace("_", " ") in text:
            hashtags.append("#" + word)

    if not hashtags:
        hashtags.append("#اخبار_فناوری")

    return " ".join(hashtags)


def get_persian_tone_name(tone: str) -> str:
    """تبدیل کلید انگلیسی لحن به نام فارسی همراه با اموجی جهت نمایش زنده روی دکمه پنل"""
    if tone == "official":
        return "👔 رسمی"
    elif tone == "friendly":
        return "🤙 صمیمی"
    elif tone == "funny":
        return "🤪 شوخی"
    return "👔 رسمی"


async def send_safe_news(
    app_bot,
    chat_id,
    text: str,
    image_data=None,
    fallback_url: str = "",
    reply_markup=None
):
    """
    ارسال امن خبر به تلگرام

    ترتیب تلاش:
    1. تصویر AI
    2. تصویر fallback سایت
    3. متن خبر
    """

    MAX_CAPTION_LENGTH = 1000
    MAX_TEXT_LENGTH = 3800

    # =========================================================
    # 1. تلاش برای ارسال تصویر AI
    # =========================================================

    if image_data:

        print(
            f"[SEND] Trying AI image -> chat_id={chat_id}",
            flush=True
        )

        try:

            photo_file = io.BytesIO(image_data)
            photo_file.name = "news.jpg"

            if len(text) <= MAX_CAPTION_LENGTH:

                message = await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )

                print(
                    "[SEND SUCCESS] AI image + caption",
                    flush=True
                )

                return message

            else:

                await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file
                )

                print(
                    "[SEND SUCCESS] AI image only",
                    flush=True
                )

        except Exception as e:

            print(
                f"[AI IMAGE FAILED] {e}",
                flush=True
            )

    # =========================================================
    # 2. تلاش برای ارسال تصویر fallback
    # =========================================================

    if fallback_url:

        print(
            f"[SEND] Trying fallback image -> {fallback_url}",
            flush=True
        )

        try:

            if len(text) <= MAX_CAPTION_LENGTH:

                message = await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=fallback_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )

                print(
                    "[SEND SUCCESS] Fallback image + caption",
                    flush=True
                )

                return message

            else:

                await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=fallback_url
                )

                print(
                    "[SEND SUCCESS] Fallback image only",
                    flush=True
                )

        except Exception as e:

            print(
                f"[FALLBACK IMAGE FAILED] {e}",
                flush=True
            )

    # =========================================================
    # 3. ارسال متن خبر
    # =========================================================

    print(
        f"[SEND] Trying text message -> chat_id={chat_id}",
        flush=True
    )

    try:

        if len(text) <= MAX_TEXT_LENGTH:

            message = await app_bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            print(
                "[SEND SUCCESS] Text message",
                flush=True
            )

            return message

        # -----------------------------------------------------
        # متن طولانی
        # -----------------------------------------------------

        chunks = [
            text[i:i + MAX_TEXT_LENGTH]
            for i in range(
                0,
                len(text),
                MAX_TEXT_LENGTH
            )
        ]

        last_message = None

        for index, chunk in enumerate(chunks):

            current_markup = (
                reply_markup
                if index == len(chunks) - 1
                else None
            )

            last_message = await app_bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="HTML",
                reply_markup=current_markup
            )

        print(
            "[SEND SUCCESS] Long text message",
            flush=True
        )

        return last_message

    except Exception as e:

        print(
            f"[SEND ERROR] {e}",
            flush=True
        )

        try:

            diagnostic["telegram"] = str(e)

        except Exception:
            pass

        return None
# =============================================================
# بخش موتور اصلی ربات (اسکرپ موازی و ۳ تایی اخبار)
# =============================================================
async def check_and_process_news(app_bot) -> None:
    """
    جمع‌آوری اخبار از اسکرپرها، اعمال فیلتر،
    ذخیره در صف و پردازش حداکثر ۱۰ خبر توسط AI در هر ساعت.
    """

    global diagnostic

    try:

        # ==================================================
        # بررسی وضعیت ربات
        # ==================================================

        if database.get_setting("bot_status") == "OFF":
            print("[SYSTEM] Bot is OFF")
            return

        print("[SYSTEM] شروع بررسی اخبار...")

        all_articles = []

        diagnostic["techcrunch"] = 0
        diagnostic["zoomit"] = 0
        diagnostic["digiato"] = 0

        # ==================================================
        # TechCrunch
        # ==================================================

        try:

            tc_articles = scrape_techcrunch()

            diagnostic["techcrunch"] = len(tc_articles)

            all_articles.extend(tc_articles)

            print(
                f"[SCRAPER] TechCrunch -> "
                f"{len(tc_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"TechCrunch: {e}"

            print(
                f"[TECHCRUNCH ERROR] {e}"
            )

        # ==================================================
        # Zoomit
        # ==================================================

        try:

            zoomit_articles = scrape_zoomit()

            diagnostic["zoomit"] = len(zoomit_articles)

            all_articles.extend(zoomit_articles)

            print(
                f"[SCRAPER] Zoomit -> "
                f"{len(zoomit_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"Zoomit: {e}"

            print(
                f"[ZOOMIT ERROR] {e}"
            )

        # ==================================================
        # Digiato
        # ==================================================

        try:

            digiato_articles = scrape_digiato()

            diagnostic["digiato"] = len(digiato_articles)

            all_articles.extend(digiato_articles)

            print(
                f"[SCRAPER] Digiato -> "
                f"{len(digiato_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"Digiato: {e}"

            print(
                f"[DIGIATO ERROR] {e}"
            )

        # ==================================================
        # اگر هیچ خبری پیدا نشد
        # ==================================================

        if not all_articles:

            print(
                "[SYSTEM] هیچ خبری پیدا نشد"
            )

            diagnostic["last_error"] = "No articles found"

        else:

            print(
                f"[SYSTEM] مجموع اخبار پیدا شده: "
                f"{len(all_articles)}"
            )

        # ==================================================
        # مرحله اول:
        # فیلتر و ورود اخبار جدید به صف
        # ==================================================

        for art in all_articles:

            try:

                title = art.get(
                    "title",
                    "بدون عنوان"
                )

                url = art.get(
                    "url",
                    ""
                )

                content = art.get(
                    "content",
                    ""
                )

                source = art.get(
                    "source",
                    "نامشخص"
                )

                image = art.get(
                    "image",
                    ""
                )

                print(
                    f"[PROCESSING] "
                    f"{source} -> {title}"
                )

                # ------------------------------------------
                # بررسی URL پردازش‌شده
                # ------------------------------------------

                if url and database.is_url_processed(url):

                    print(
                        f"[SKIPPED] قبلاً پردازش شده: "
                        f"{title}"
                    )

                    continue

                # ------------------------------------------
                # فیلتر تکنولوژی
                # ------------------------------------------

                print(
                    f"[FILTER CHECK] {title}"
                )

                result = is_technology_relevant(
                    title,
                    content
                )

                print(
                    f"[FILTER RESULT] {result}"
                )

                if not result:

                    print(
                        f"[FILTERED] {title}"
                    )

                    continue

                # ------------------------------------------
                # اضافه کردن به صف
                # ------------------------------------------

                database.add_news_to_queue(
                    url=url,
                    title=title,
                    content=content,
                    image=image,
                    source=source
                )

                print(
                    f"[QUEUE ADDED] {title}"
                )

            except Exception as article_error:

                diagnostic["last_error"] = str(
                    article_error
                )

                print(
                    f"[QUEUE ARTICLE ERROR] "
                    f"{article_error}"
                )

                continue

        # ==================================================
        # مرحله دوم:
        # پردازش صف
        # ==================================================

        print(
            "[QUEUE] شروع پردازش صف اخبار..."
        )

        # ==================================================
        # حداکثر تعداد پردازش در این اجرا
        # ==================================================

        processed_this_run = 0

        while True:

            # --------------------------------------------------
            # بررسی سهمیه ساعتی
            # --------------------------------------------------

            if not database.can_use_ai_hourly_limit(10):
                print(
                    "[QUEUE] سهمیه AI در این ساعت "
                    "به پایان رسیده است."
                )

                break

            # --------------------------------------------------
            # دریافت قدیمی‌ترین خبر منتظر
            # --------------------------------------------------

            pending_queue = database.get_pending_news(
                limit=1
            )

            if not pending_queue:
                print(
                    "[QUEUE] صف پردازش خالی است."
                )
                break

            news = pending_queue[0]

            news_id = news[0]
            url = news[1]
            title = news[2]
            content = news[3]
            image = news[4]
            source = news[5]

            print(
                f"[QUEUE PROCESSING] "
                f"{source} -> {title}"
            )

            # --------------------------------------------------
            # جلوگیری از پردازش مجدد URL
            # --------------------------------------------------

            if url and database.is_url_processed(url):

                print(
                    f"[QUEUE SKIPPED] "
                    f"قبلاً پردازش شده: {title}"
                )

                continue

            # --------------------------------------------------
            # تغییر وضعیت به processing
            # --------------------------------------------------

            database.mark_news_processing(
                news_id
            )

            print(
                f"[AI START] {title}"
            )

            # --------------------------------------------------
            # ارسال به Gemini
            # --------------------------------------------------

            ai_text = process_news_with_ai(
                content
            )

            # --------------------------------------------------
            # خطای AI
            # --------------------------------------------------

            if not ai_text:

                database.mark_news_pending(
                    news_id
                )

                print(
                    f"[AI FAILED] {title}"
                )

                # این خبر دوباره در صف باقی می‌ماند
                # و در اجرای بعدی مجدداً امتحان می‌شود.

                break

            # --------------------------------------------------
            # موفقیت AI
            # --------------------------------------------------

            processed_this_run += 1

            print(
                f"[AI SUCCESS] {title}"
            )

            # --------------------------------------------------
            # ساخت پیش‌نویس
            # --------------------------------------------------

            ai_image = None

            preview_news_id = str(news_id)

            hashtags = generate_hashtags(
                ai_text
            )

            pending_news[
                preview_news_id
            ] = {
                "url": url,
                "title": title,
                "text": ai_text,
                "ai_text": ai_text,
                "ai_image": ai_image,
                "fallback_image": image
            }

            # --------------------------------------------------
            # دکمه‌های مدیریت خبر
            # --------------------------------------------------

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔥 برچسب فوری",
                        callback_data=(
                            f"urgent_{preview_news_id}"
                        )
                    ),
                    InlineKeyboardButton(
                        "✅ ارسال عادی",
                        callback_data=(
                            f"normal_{preview_news_id}"
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✏️ دوباره ویرایش کن",
                        callback_data=(
                            f"edit_{preview_news_id}"
                        )
                    ),
                    InlineKeyboardButton(
                        "❌ حذف و رد کردن",
                        callback_data=(
                            f"skip_{preview_news_id}"
                        )
                    )
                ]
            ]

            # --------------------------------------------------
            # متن پیش‌نمایش
            # --------------------------------------------------

            preview_text = (
                f"📰 <b>پیش‌نویس خبر "
                f"({html.escape(source)})</b>\n\n"
                f"{clean_html_formatting(ai_text)}"
                f"\n\n"
                f"{hashtags}"
                f"\n\n"
                f"<b>لینک:</b>\n"
                f"{html.escape(url)}"
            )

            # --------------------------------------------------
            # ارسال پیش‌نمایش برای ادمین
            # --------------------------------------------------
            print(
                f"[PREVIEW START] ارسال پیش‌نمایش برای ادمین: {ADMIN_TELEGRAM_ID}"
            )
            await send_safe_news(
                app_bot,
                ADMIN_TELEGRAM_ID,
                preview_text,
                ai_image,
                image,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

            print(
                f"[PREVIEW RETURNED] تابع send_safe_news برگشت: {title}"
            )
            
            print(
                f"[PREVIEW SENT] {title}"
            )

            # --------------------------------------------------
            # اگر به ۱۰ خبر در این اجرا رسیدیم
            # --------------------------------------------------

            if processed_this_run >= 10:

                print(
                    "[QUEUE] سقف ۱۰ خبر برای این چرخه "
                    "پردازش شد."
                )

                break

    except Exception as e:

        diagnostic["last_error"] = str(e)

        print(
            f"[SYSTEM ERROR] "
            f"{e}"
        )
# -------------------------------------------------------------
# بخش کنترل پنل ادمین و مدیریت دکمه‌های تلگرام
# -------------------------------------------------------------
async def start_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    user_id = update.effective_user.id

    try:

        # =========================
        # بررسی دسترسی ادمین
        # =========================

        is_admin = (
            user_id == ADMIN_TELEGRAM_ID
            or database.is_user_admin(user_id)
        )

        if not is_admin:

            await update.message.reply_text(
                "🔒 <b>دسترسی محدود است!</b>\n\n"
                "لطفاً رمز عبور مدیریت ربات را ارسال کنید.",
                parse_mode="HTML"
            )

            return

        # =========================
        # دریافت وضعیت سیستم
        # =========================

        status = database.get_setting("bot_status") or "ON"
        tone = database.get_setting("bot_tone") or "official"

        persian_tone = get_persian_tone_name(tone)

        # =========================
        # ساخت پنل مدیریت
        # =========================

        keyboard = [
            [
                InlineKeyboardButton(
                    f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}",
                    callback_data="toggle_status"
                ),
                InlineKeyboardButton(
                    f"لحن: {persian_tone}",
                    callback_data="toggle_tone"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 آمار",
                    callback_data="view_stats"
                ),
                InlineKeyboardButton(
                    "🔄 اخبار",
                    callback_data="run_now"
                )
            ],
            [
                InlineKeyboardButton(
                    "📰 اخبار پردازش‌شده",
                    callback_data="completed_news"
                )
            ],
            [
                InlineKeyboardButton(
                    "🩺 عیب‌یابی",
                    callback_data="diagnostic"
                )
            ]
        ]

        await update.message.reply_text(
            "🎛 <b>به پنل مدیریت سیستم هوشمند ۳ موتوره خوش آمدید.</b>\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

        print(
            f"[ADMIN] Panel opened by user {user_id}"
        )

    except Exception as e:

        print(
            f"[START PANEL ERROR] {e}"
        )

        diagnostic["last_error"] = (
            f"Start Panel: {e}"
        )

        await update.message.reply_text(
            "❌ خطایی هنگام باز کردن پنل مدیریت رخ داد."
        )

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت پیام‌های متنی چت: تفکیک بین وضعیت ادمین در حال ویرایش خبر یا کاربر در حال ارسال رمز عبور"""
    try:
        user_id = update.effective_user.id
        incoming_text = update.message.text

        if user_id in user_editing_state:
            news_id = user_editing_state[user_id]
            if news_id in pending_news:
                pending_news[news_id]["text"] = incoming_text
                keyboard = [[InlineKeyboardButton("🔥 برچسب فوری", callback_data=f"urgent_{news_id}"),
                             InlineKeyboardButton("✅ ارسال عادی", callback_data=f"normal_{news_id}")],
                            [InlineKeyboardButton("✏️ دوباره ویرایش کن", callback_data=f"edit_{news_id}"),
                             InlineKeyboardButton("❌ حذف و رد کردن", callback_data=f"skip_{news_id}")]]
                safe_text = clean_html_formatting(incoming_text)
                preview_msg = f"📝 <b>پیش‌نویس خبر ویرایش و اصلاح شد:</b>\n\n{safe_text}\n\n<b>لینک اصلی:</b>\n{html.escape(pending_news[news_id]['url'])}"
                await send_safe_news(context.application.bot, user_id, preview_msg,
                                     pending_news[news_id].get("ai_image"), pending_news[news_id].get("fallback_image"),
                                     reply_markup=InlineKeyboardMarkup(keyboard))
            if user_id in user_editing_state: del user_editing_state[user_id]
            return

        if incoming_text == ADMIN_PASSWORD:
            database.add_authenticated_admin(user_id)
            await update.message.reply_text(
    "🔓 <b>هویت شما با موفقیت تایید شد!</b>\n\n"
    "اکنون برای باز شدن پنل مدیریت، مجدداً دستور /start را ارسال کنید.",
    parse_mode="HTML"
)
        elif user_id != ADMIN_TELEGRAM_ID and not database.is_user_admin(user_id):
            await update.message.reply_text("❌ <b>رمز عبور اشتباه است!</b> دسترسی صادر نشد.")
    except Exception:
        pass

async def show_completed_news(update, context):
    """
    نمایش آخرین اخبار پردازش‌شده از دیتابیس
    """

    try:
        rows = database.get_completed_news(limit=10)

        if not rows:
            await update.message.reply_text(
                "📭 هیچ خبر پردازش‌شده‌ای وجود ندارد."
            )
            return

        text = "📰 <b>آخرین اخبار پردازش‌شده</b>\n\n"

        for news in rows:
            news_id = news[0]
            title = news[1]
            source = news[2]

            text += (
                f"🔹 <b>{html.escape(title)}</b>\n"
                f"📡 منبع: {html.escape(source)}\n"
                f"🆔 شناسه: <code>{news_id}</code>\n\n"
            )

        await update.message.reply_text(
            text,
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"[COMPLETED NEWS ERROR] {e}")

        await update.message.reply_text(
            "❌ خطا در دریافت اخبار پردازش‌شده."
        )

async def handle_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت کامل دکمه‌های پنل و تایید اخبار"""

    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        if user_id != ADMIN_TELEGRAM_ID and not database.is_user_admin(user_id):
            await query.answer(
                "🔒 شما دسترسی مدیریت ندارید!",
                show_alert=True
            )
            return

        # =========================
        # پنل مدیریت
        # =========================

        if data == "toggle_status":

            current = database.get_setting("bot_status")
            new_status = "OFF" if current == "ON" else "ON"

            database.update_setting(
                "bot_status",
                new_status
            )

            status = new_status
            tone = database.get_setting("bot_tone")

            persian_tone = get_persian_tone_name(tone)

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}",
                        callback_data="toggle_status"
                    ),
                    InlineKeyboardButton(
                        f"لحن: {persian_tone}",
                        callback_data="toggle_tone"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 آمار",
                        callback_data="view_stats"
                    ),
                    InlineKeyboardButton(
                        "🔄 اخبار",
                        callback_data="run_now"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🩺 عیب‌یابی",
                        callback_data="diagnostic"
                    )
                ]
            ]

            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "toggle_tone":

            current = database.get_setting("bot_tone")

            if current == "official":
                new_tone = "friendly"
            elif current == "friendly":
                new_tone = "funny"
            else:
                new_tone = "official"

            database.update_setting(
                "bot_tone",
                new_tone
            )

            status = database.get_setting("bot_status")
            persian_tone = get_persian_tone_name(new_tone)

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}",
                        callback_data="toggle_status"
                    ),
                    InlineKeyboardButton(
                        f"لحن: {persian_tone}",
                        callback_data="toggle_tone"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 آمار",
                        callback_data="view_stats"
                    ),
                    InlineKeyboardButton(
                        "🔄 اخبار",
                        callback_data="run_now"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🩺 عیب‌یابی",
                        callback_data="diagnostic"
                    )
                ]
            ]

            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "view_stats":

            articles, tokens = database.get_today_stats()

            await query.message.reply_text(
                f"📊 آمار امروز\n\n"
                f"تعداد اخبار: {articles}\n"
                f"توکن مصرفی: {tokens}"
            )

        elif data == "run_now":

            await query.message.reply_text(
                "⏳ شروع پردازش اخبار..."
            )

            await check_and_process_news(
                context.application.bot
            )

        elif data == "completed_news":

            try:

                rows = database.get_completed_news(
                    limit=10
                )

                if not rows:
                    await query.message.reply_text(
                        "📭 هیچ خبر پردازش‌شده‌ای وجود ندارد."
                    )

                    return

                text = (
                    "📰 <b>آخرین اخبار پردازش‌شده</b>\n\n"
                )

                for news in rows:
                    news_id = news[0]
                    title = news[1]
                    source = news[2]
                    processed_at = news[4]

                    text += (
                        f"🔹 <b>{html.escape(title)}</b>\n"
                        f"📡 منبع: {html.escape(source)}</b>\n"
                        f"🕐 زمان پردازش: "
                        f"{html.escape(str(processed_at))}\n"
                        f"🆔 شناسه: <code>{news_id}</code>\n\n"
                    )

                await query.message.reply_text(
                    text,
                    parse_mode="HTML"
                )

            except Exception as e:

                print(
                    f"[COMPLETED NEWS ERROR] {e}"
                )

                await query.message.reply_text(
                    "❌ خطا در دریافت اخبار پردازش‌شده."
                )

        elif data == "completed_news":

            try:

                rows = database.get_completed_news(
                    limit=10
                )

                if not rows:
                    await query.message.reply_text(
                        "📭 هیچ خبر پردازش‌شده‌ای وجود ندارد."
                    )

                    return

                text = (
                    "📰 <b>آخرین اخبار پردازش‌شده</b>\n\n"
                )

                for news in rows:
                    news_id = news[0]
                    title = news[1]
                    source = news[2]
                    processed_at = news[4]

                    text += (
                        f"🔹 <b>{html.escape(title)}</b>\n"
                        f"📡 منبع: <b>{html.escape(source)}</b>\n"
                        f"🕐 زمان پردازش: "
                        f"{html.escape(str(processed_at))}\n"
                        f"🆔 شناسه: <code>{news_id}</code>\n\n"
                    )

                await query.message.reply_text(
                    text,
                    parse_mode="HTML"
                )

            except Exception as e:

                print(
                    f"[COMPLETED NEWS ERROR] {e}"
                )

                await query.message.reply_text(
                    "❌ خطا در دریافت اخبار پردازش‌شده."
                )

        elif data == "completed_news":

            try:

                rows = database.get_completed_news(
                    limit=10
                )

                if not rows:
                    await query.message.reply_text(
                        "📭 هیچ خبر پردازش‌شده‌ای وجود ندارد."
                    )

                    return

                text = (
                    "📰 <b>آخرین اخبار پردازش‌شده</b>\n\n"
                )

                for news in rows:
                    news_id = news[0]
                    title = news[1]
                    source = news[2]
                    processed_at = news[4]

                    text += (
                        f"🔹 <b>{html.escape(title)}</b>\n"
                        f"📡 منبع: <b>{html.escape(source)}</b>\n"
                        f"🕐 زمان پردازش: "
                        f"{html.escape(str(processed_at))}\n"
                        f"🆔 شناسه: <code>{news_id}</code>\n\n"
                    )

                await query.message.reply_text(
                    text,
                    parse_mode="HTML"
                )

            except Exception as e:

                print(
                    f"[COMPLETED NEWS ERROR] {e}"
                )

                await query.message.reply_text(
                    "❌ خطا در دریافت اخبار پردازش‌شده."
                )


        elif data == "diagnostic":

            report = (
                f"🩺 گزارش سلامت سیستم\n\n"
                f"TechCrunch: {diagnostic.get('techcrunch',0)}\n"
                f"Zoomit: {diagnostic.get('zoomit',0)}\n"
                f"Digiato: {diagnostic.get('digiato',0)}\n\n"
                f"Gemini:\n{diagnostic.get('gemini','OK')}\n\n"
                f"Image AI:\n{diagnostic.get('image_ai','OK')}\n\n"
                f"Telegram:\n{diagnostic.get('telegram','OK')}\n\n"
                f"Last Error:\n{diagnostic.get('last_error','-')}"
            )

            await query.message.reply_text(report)

        # =========================
        # دکمه‌های خبر
        # =========================

        elif data.startswith("normal_"):

            print(

                f"[BUTTON] normal_ clicked: {data}",

                flush=True

            )

            news_id = data.replace("normal_", "")

            print(

                f"[BUTTON] extracted news_id: {news_id}",

                flush=True

            )

            # =========================================================

            # بررسی وجود خبر در حافظه

            # =========================================================

            if news_id not in pending_news:
                print(

                    f"[BUTTON ERROR] news_id not found: {news_id}",

                    flush=True

                )

                await query.message.reply_text(

                    "❌ این خبر دیگر در حافظه ربات وجود ندارد."

                )

                return

            print(

                f"[BUTTON] news found: {news_id}",

                flush=True

            )

            news = pending_news[news_id]

            print(

                f"[BUTTON] title: {news.get('title', '-')}",

                flush=True

            )

            print(

                f"[BUTTON] channel: {TELEGRAM_CHANNEL_ID}",

                flush=True

            )

            # =========================================================

            # ارسال خبر به کانال

            # =========================================================

            print(

                "[BUTTON] Calling send_safe_news...",

                flush=True

            )

            sent_message = await send_safe_news(

                context.application.bot,

                TELEGRAM_CHANNEL_ID,

                news["text"],

                news.get("ai_image"),

                news.get("fallback_image", "")

            )

            # =========================================================

            # بررسی نتیجه ارسال

            # =========================================================

            if not sent_message:
                print(

                    f"[BUTTON ERROR] send_safe_news returned None: {news_id}",

                    flush=True

                )

                await query.message.reply_text(

                    "❌ ارسال خبر به کانال ناموفق بود."

                )

                return

            print(

                f"[BUTTON] Channel send SUCCESS: {news_id}",

                flush=True

            )

            # =========================================================

            # ثبت URL به عنوان پردازش‌شده

            # =========================================================

            try:

                database.mark_url_as_processed(

                    news["url"],

                    news["title"]

                )

                print(

                    f"[DATABASE] URL marked processed: {news_id}",

                    flush=True

                )


            except Exception as e:

                print(

                    f"[DATABASE ERROR] mark_url_as_processed: {e}",

                    flush=True

                )

            # =========================================================

            # تغییر وضعیت خبر به completed

            # =========================================================

            try:

                database.mark_news_completed(

                    int(news_id)

                )

                print(

                    f"[DATABASE] News marked completed: {news_id}",

                    flush=True

                )


            except Exception as e:

                print(

                    f"[DATABASE ERROR] mark_news_completed: {e}",

                    flush=True

                )

            # =========================================================

            # حذف خبر از حافظه

            # =========================================================

            if news_id in pending_news:
                del pending_news[news_id]

            print(

                f"[BUTTON] pending_news removed: {news_id}",

                flush=True

            )

            # =========================================================

            # اطلاع به ادمین

            # =========================================================

            await query.message.reply_text(

                "✅ خبر با موفقیت به کانال ارسال شد."

            )

        elif data.startswith("urgent_"):

            news_id = data.replace("urgent_", "")

            if news_id not in pending_news:
                return

            news = pending_news[news_id]

            # --------------------------------------------------

            # ساخت متن خبر فوری

            # --------------------------------------------------

            urgent_text = (

                    "🚨 خبر فوری\n\n"

                    + news["text"]

            )

            # --------------------------------------------------

            # ارسال خبر به کانال

            # --------------------------------------------------

            sent_message = await send_safe_news(

                context.application.bot,

                TELEGRAM_CHANNEL_ID,

                urgent_text,

                news.get("ai_image"),

                news.get("fallback_image", "")

            )

            # --------------------------------------------------

            # بررسی موفقیت ارسال

            # --------------------------------------------------

            if not sent_message:
                await query.message.reply_text(

                    "❌ ارسال خبر فوری به کانال ناموفق بود."

                )

                return

            # --------------------------------------------------

            # تلاش برای Pin کردن خبر

            # --------------------------------------------------

            try:

                await context.application.bot.pin_chat_message(

                    TELEGRAM_CHANNEL_ID,

                    sent_message.message_id

                )


            except Exception as pin_error:

                print(

                    f"[PIN ERROR] {pin_error}"

                )

            # --------------------------------------------------

            # ثبت URL به عنوان پردازش‌شده

            # --------------------------------------------------

            database.mark_url_as_processed(

                news["url"],

                news["title"]

            )

            # --------------------------------------------------

            # تغییر وضعیت خبر به completed

            # --------------------------------------------------

            database.mark_news_completed(

                int(news_id)

            )

            # --------------------------------------------------

            # حذف پیش‌نویس از حافظه

            # --------------------------------------------------

            del pending_news[news_id]

            # --------------------------------------------------

            # اطلاع به ادمین

            # --------------------------------------------------

            await query.message.reply_text(

                "🚨 خبر فوری ارسال و پین شد."

            )

        elif data.startswith("edit_"):

            news_id = data.replace("edit_", "")

            user_editing_state[user_id] = news_id

            await query.message.reply_text(
                "✏️ متن جدید خبر را ارسال کنید."
            )

        elif data.startswith("skip_"):

            news_id = data.replace("skip_", "")

            if news_id in pending_news:
                del pending_news[news_id]

            await query.message.reply_text(
                "❌ خبر حذف شد."
            )

    except Exception as e:

        print(
            f"[BUTTON ERROR] {e}"
        )


async def periodic_news_check(context: ContextTypes.DEFAULT_TYPE):
    """بررسی دوره‌ای اخبار"""
    await check_and_process_news(context.bot)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start_panel)
    )

    application.add_handler(
        CallbackQueryHandler(handle_panel_buttons)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_messages
        )
    )

    application.job_queue.run_repeating(
        periodic_news_check,
        interval=900,
        first=10
    )

    print("[SYSTEM] Telegram Bot Started")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
