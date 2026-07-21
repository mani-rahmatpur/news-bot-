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
    ارسال امن خبر به تلگرام با مدیریت خطاها
    """

    try:
        MAX_CAPTION_LENGTH = 1000
        MAX_TEXT_LENGTH = 3800

        # ابتدا تلاش برای ارسال عکس تولید شده توسط AI
        if image_data:
            try:
                photo_file = io.BytesIO(image_data)
                photo_file.name = "news.jpg"

                if len(text) <= MAX_CAPTION_LENGTH:
                    return await app_bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )

                await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file
                )

            except Exception as photo_err:
                print(f"[PHOTO ERROR] {photo_err}")

        # اگر عکس AI نبود از عکس سایت استفاده کن
        elif fallback_url:
            try:
                if len(text) <= MAX_CAPTION_LENGTH:
                    return await app_bot.send_photo(
                        chat_id=chat_id,
                        photo=fallback_url,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )

                await app_bot.send_photo(
                    chat_id=chat_id,
                    photo=fallback_url
                )

            except Exception as fallback_err:
                print(f"[FALLBACK PHOTO ERROR] {fallback_err}")

        # ارسال متن
        if len(text) <= MAX_TEXT_LENGTH:
            return await app_bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        # اگر متن خیلی بلند بود تقسیم شود
        chunks = [
            text[i:i + MAX_TEXT_LENGTH]
            for i in range(0, len(text), MAX_TEXT_LENGTH)
        ]

        for index, chunk in enumerate(chunks):

            current_markup = (
                reply_markup
                if index == len(chunks) - 1
                else None
            )

            await app_bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="HTML",
                reply_markup=current_markup
            )

        return True


    except Exception as send_err:

        print(f"[SEND ERROR] {send_err}")

        try:

            import main

            main.diagnostic["telegram"] = str(send_err)

        except:

            pass

# =============================================================
# بخش موتور اصلی ربات (اسکرپ موازی و ۳ تایی اخبار)
# =============================================================
async def check_and_process_news(app_bot) -> None:
    """
    جمع‌آوری، پردازش و ارسال پیش‌نمایش اخبار
    نسخه پایدار با لاگ و عیب‌یابی کامل
    """

    global diagnostic

    try:

        if database.get_setting("bot_status") == "OFF":
            print("[SYSTEM] Bot is OFF")
            return

        print("[SYSTEM] شروع بررسی اخبار...")

        all_articles = []

        diagnostic["techcrunch"] = 0
        diagnostic["zoomit"] = 0
        diagnostic["digiato"] = 0

        # -------------------------
        # TechCrunch
        # -------------------------

        try:
            tc_articles = scrape_techcrunch()

            diagnostic["techcrunch"] = len(tc_articles)

            all_articles.extend(tc_articles)

            print(
                f"[SCRAPER] TechCrunch -> {len(tc_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"TechCrunch: {e}"

            print(f"[TECHCRUNCH ERROR] {e}")

        # -------------------------
        # Zoomit
        # -------------------------

        try:
            zoomit_articles = scrape_zoomit()

            diagnostic["zoomit"] = len(zoomit_articles)

            all_articles.extend(zoomit_articles)

            print(
                f"[SCRAPER] Zoomit -> {len(zoomit_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"Zoomit: {e}"

            print(f"[ZOOMIT ERROR] {e}")

        # -------------------------
        # Digiato
        # -------------------------

        try:
            digiato_articles = scrape_digiato()

            diagnostic["digiato"] = len(digiato_articles)

            all_articles.extend(digiato_articles)

            print(
                f"[SCRAPER] Digiato -> {len(digiato_articles)} article(s)"
            )

        except Exception as e:

            diagnostic["last_error"] = f"Digiato: {e}"

            print(f"[DIGIATO ERROR] {e}")

        # -------------------------

        if not all_articles:

            print("[SYSTEM] هیچ خبری پیدا نشد")

            diagnostic["last_error"] = "No articles found"

            return

        print(
            f"[SYSTEM] مجموع اخبار پیدا شده: {len(all_articles)}"
        )

        # ==================================================
        # پردازش اخبار
        # ==================================================

        for art in all_articles:

            try:

                title = art.get("title", "بدون عنوان")
                url = art.get("url", "")
                content = art.get("content", "")
                source = art.get("source", "نامشخص")

                print(
                    f"[PROCESSING] {source} -> {title}"
                )

                # جلوگیری از تکرار

                if url and database.is_url_processed(url):

                    print(
                        f"[SKIPPED] قبلاً ارسال شده: {title}"
                    )

                    continue

                # ------------------
                # AI
                # ------------------
                print("\n===================")
                print("TITLE:", title)
                print("CONTENT PREVIEW:")
                print(content[:1000])
                print("===================\n")
                ai_text = process_news_with_ai(content)

                if not ai_text:
                    print(
                        f"[AI FALLBACK] {title}"
                    )

                    ai_text = (
                        f"📰 {title}\n\n"
                        f"{content[:1500]}\n\n"
                        f"🏷 #TechFlow #IranNFT"
                    )
                # ------------------
                # IMAGE
                # ------------------

                ai_image = None

                news_id = str(hash(url))

                status = database.get_setting("bot_status") or "ON"

                tone = database.get_setting("tone") or "formal"
                persian_tone = get_persian_tone_name(tone)

                hashtags = generate_hashtags(ai_text)

                pending_news[news_id] = {
                    "url": url,
                    "title": title,
                    "text": ai_text,
                    "ai_text": ai_text,
                    "ai_image": ai_image,
                    "fallback_image": art.get("image", "")
                }

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔥 برچسب فوری",
                            callback_data=f"urgent_{news_id}"
                        ),
                        InlineKeyboardButton(
                            "✅ ارسال عادی",
                            callback_data=f"normal_{news_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✏️ دوباره ویرایش کن",
                            callback_data=f"edit_{news_id}"
                        ),
                        InlineKeyboardButton(
                            "❌ حذف و رد کردن",
                            callback_data=f"skip_{news_id}"
                        )
                    ]
                ]

                preview_text = (
                    f"📰 <b>پیش‌نویس خبر ({source})</b>\n\n"
                    f"{clean_html_formatting(ai_text)}\n\n"
                    f"{hashtags}\n\n"
                    f"<b>لینک:</b>\n"
                    f"{html.escape(url)}"
                )

                await send_safe_news(
                    app_bot,
                    ADMIN_TELEGRAM_ID,
                    preview_text,
                    ai_image,
                    art.get("image", ""),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

                print(
                    f"[PREVIEW SENT] {title}"
                )

            except Exception as article_error:

                diagnostic["last_error"] = str(article_error)

                print(
                    f"[ARTICLE ERROR] {article_error}"
                )

                continue

        print("[SYSTEM] پایان چرخه پردازش اخبار")

    except Exception as e:

        diagnostic["last_error"] = str(e)

        print(
            f"[FATAL ERROR] {e}"
        )
# -------------------------------------------------------------
# بخش کنترل پنل ادمین و مدیریت دکمه‌های تلگرام
# -------------------------------------------------------------
async def start_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش پنل کنترل ادمین با ارسال دستور /start (بررسی سطح دسترسی با رمز عبور)"""
    try:
        user_id = update.effective_user.id
        await update.message.reply_text(
            f"Your Telegram ID: {user_id}"
        )

        if user_id == ADMIN_TELEGRAM_ID or database.is_user_admin(user_id):
            status = database.get_setting("bot_status")
            tone = database.get_setting("bot_tone")
            persian_tone = get_persian_tone_name(tone)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔥 برچسب فوری",
                        callback_data=f"urgent_{news_id}"
                    ),
                    InlineKeyboardButton(
                        "✅ ارسال عادی",
                        callback_data=f"normal_{news_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✏️ دوباره ویرایش کن",
                        callback_data=f"edit_{news_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ حذف و رد کردن",
                        callback_data=f"skip_{news_id}"
                    )
                ]
            ]
            await update.message.reply_text("🎛 <b>به پنل مدیریت سیستم هوشمند ۳ موتوره خوش آمدید:</b>",
                                            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        else:
            await update.message.reply_text("🔒 <b>دسترسی محدود است!</b>\nلطفاً رمز عبور مدیریت ربات را ارسال کنید:")
    except Exception:
        pass


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
                "🔓 <b>هویت شما با موفقیت تایید شد!</b>\nاکنون برای باز شدن پنل مدیریت، مجدداً دستور /start را ارسال کنید.")
        elif user_id != ADMIN_TELEGRAM_ID and not database.is_user_admin(user_id):
            await update.message.reply_text("❌ <b>رمز عبور اشتباه است!</b> دسترسی صادر نشد.")
    except Exception:
        pass


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

            news_id = data.replace("normal_", "")

            if news_id not in pending_news:
                return

            news = pending_news[news_id]

            await send_safe_news(
                context.application.bot,
                TELEGRAM_CHANNEL_ID,
                news["text"],
                news.get("ai_image"),
                news.get("fallback_image", "")
            )

            database.mark_url_as_processed(
                news["url"],
                news["title"]
            )

            del pending_news[news_id]

            await query.message.reply_text(
                "✅ خبر به کانال ارسال شد."
            )

        elif data.startswith("urgent_"):

            news_id = data.replace("urgent_", "")

            if news_id not in pending_news:
                return

            news = pending_news[news_id]

            urgent_text = (
                "🚨 خبر فوری\n\n"
                + news["text"]
            )

            msg = await send_safe_news(
                context.application.bot,
                TELEGRAM_CHANNEL_ID,
                news["ai_text"],
                news.get("ai_image"),
                news.get("fallback_image", "")
            )

            try:
                await context.application.bot.pin_chat_message(
                    TELEGRAM_CHANNEL_ID,
                    msg.message_id
                )
            except:
                pass

            database.mark_url_as_processed(
                news["url"],
                news["title"]
            )

            del pending_news[news_id]

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
