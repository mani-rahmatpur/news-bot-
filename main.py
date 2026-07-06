import logging
import asyncio
import html
import re
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import database
from ai_engine import process_news_with_ai
from scrapers.techcrunch import scrape_techcrunch
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, ADMIN_TELEGRAM_ID

# تنظیمات پایه‌ای لاگ سیستم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

pending_news = {}


def clean_html_formatting(text: str) -> str:
    """تبدیل ستاره‌های مارک‌داون به HTML استاندارد و حذف تگ‌های نامنظم مخرب"""
    text = html.escape(text)
    text = text.replace("&amp;", "&")
    pattern = re.compile(r'\*\*(.*?)\*\*')
    text = pattern.sub(r'<b>\1</b>', text)
    text = text.replace("<b></b>", "")
    return text


async def send_safe_long_message(app_bot, chat_id, text: str, reply_markup=None, is_channel=False):
    """ارسال هوشمند پیام‌ها برای جلوگیری از ارور طولانی بودن متون"""
    MAX_LENGTH = 3800
    if len(text) <= MAX_LENGTH:
        try:
            return await app_bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            return await app_bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    chunks = [text[i:i + MAX_LENGTH] for i in range(0, len(text), MAX_LENGTH)]
    first_msg = None
    for idx, chunk in enumerate(chunks):
        current_markup = reply_markup if idx == len(chunks) - 1 else None
        try:
            msg = await app_bot.send_message(chat_id=chat_id, text=chunk, reply_markup=current_markup,
                                             parse_mode="HTML")
        except Exception:
            msg = await app_bot.send_message(chat_id=chat_id, text=chunk, reply_markup=current_markup)
        if idx == 0 and is_channel:
            first_msg = msg
    return first_msg if is_channel else None


# ==========================================
# بخش موتور اصلی ربات (اسکرپ و پردازش)
# ==========================================
async def check_and_process_news(app_bot) -> None:
    if database.get_setting("bot_status") == "OFF":
        print("[SYSTEM] ربات خاموش است. عملیات اسکرپ انجام نشد.")
        return

    print("[SYSTEM] اسکرپر در حال جستجوی اخبار تکنولوژی...")
    articles = scrape_techcrunch()

    for art in articles:
        print(f"[SYSTEM] ارسال به هوش مصنوعی برای پردازش خبر: {art['title']}")
        ai_text = process_news_with_ai(art["content"])

        if ai_text:
            news_id = str(hash(art["url"]))
            pending_news[news_id] = {
                "url": art["url"],
                "title": art["title"],
                "text": ai_text
            }

            keyboard = [
                [
                    InlineKeyboardButton("🔥 برچسب فوری بزن", callback_data=f"urgent_{news_id}"),
                    InlineKeyboardButton("✅ ارسال عادی", callback_data=f"normal_{news_id}")
                ],
                [InlineKeyboardButton("❌ حذف و نادیده گرفتن", callback_data=f"skip_{news_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            safe_text = clean_html_formatting(ai_text)
            preview_msg = f"📰 <b>پیش‌نویس خبر جدید توسط هوش مصنوعی:</b>\n\n{safe_text}\n\n<b>لینک اصلی:</b>\n{html.escape(art['url'])}"

            await send_safe_long_message(app_bot, ADMIN_TELEGRAM_ID, preview_msg, reply_markup=reply_markup)


def run_scheduler(loop, app_bot):
    """انتقال امن عملیات کرون‌جاب به لوپ اصلی سیستم Asyncio"""
    asyncio.run_coroutine_threadsafe(check_and_process_news(app_bot), loop)


# ==========================================
# بخش کنترل پنل ادمین (دکمه‌های ربات تلگرام)
# ==========================================
async def start_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return

    status = database.get_setting("bot_status")
    tone = database.get_setting("bot_tone")

    keyboard = [
        [
            InlineKeyboardButton(f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}", callback_data="toggle_status"),
            InlineKeyboardButton(f"لحن: {'👔 رسمی' if tone == 'official' else '🤙 صمیمی'}", callback_data="toggle_tone")
        ],
        [
            InlineKeyboardButton("🔄 پردازش اخبار", callback_data="run_now"),
            InlineKeyboardButton("📊 گزارش آمار امروز", callback_data="view_stats")
        ]
    ]
    await update.message.reply_text("🎛 <b>به پنل مدیریت سیستم هوشمند خوش آمدید:</b>",
                                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def handle_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    if data == "toggle_status":
        await query.answer()
        current = database.get_setting("bot_status")
        new_status = "OFF" if current == "ON" else "ON"
        database.update_setting("bot_status", new_status)
        status = new_status
        tone = database.get_setting("bot_tone")
        keyboard = [
            [InlineKeyboardButton(f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}", callback_data="toggle_status"),
             InlineKeyboardButton(f"لحن: {'👔 رسمی' if tone == 'official' else '🤙 صمیمی'}",
                                  callback_data="toggle_tone")],
            [InlineKeyboardButton("🔄 پردازش اخبار", callback_data="run_now"),
             InlineKeyboardButton("📊 گزارش آمار امروز", callback_data="view_stats")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "toggle_tone":
        current = database.get_setting("bot_tone")
        new_tone = "friendly" if current == "official" else "official"
        database.update_setting("bot_tone", new_tone)

        persian_tone_name = "👔 رسمی" if new_tone == "official" else "🤙 صمیمی"
        await query.answer(text=f"✨ لحن هوش مصنوعی به {persian_tone_name} تغییر کرد!", show_alert=False)

        status = database.get_setting("bot_status")
        keyboard = [
            [InlineKeyboardButton(f"وضعیت: {'🟢 روشن' if status == 'ON' else '🔴 خاموش'}", callback_data="toggle_status"),
             InlineKeyboardButton(f"لحن: {'👔 رسمی' if new_tone == 'official' else '🤙 صمیمی'}",
                                  callback_data="toggle_tone")],
            [InlineKeyboardButton("🔄 پردازش اخبار", callback_data="run_now"),
             InlineKeyboardButton("📊 گزارش آمار امروز", callback_data="view_stats")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "run_now":
        await query.answer()
        await query.message.reply_text("🔄 اسکرپر فعال شد. در حال جمع‌آوری اخبار زنده...")
        asyncio.create_task(check_and_process_news(context.application.bot))

    elif data == "view_stats":
        await query.answer()
        count, tokens = database.get_today_stats()
        await query.message.reply_text(
            f"📊 <b>گزارش عملکرد امروز:</b>\n\n• اخبار پردازش شده: {count} خبر\n• کل مصرف توکن تخمینی: {tokens} توکن",
            parse_mode="HTML")

    elif "_" in data:
        await query.answer()
        action, news_id = data.split("_")
        if news_id in pending_news:
            news_data = pending_news[news_id]
            safe_channel_text = clean_html_formatting(news_data['text'])

            if action == "urgent":
                final_text = f"🚨 🔥 <b>#فوری</b> 🔥 🚨\n\n{safe_channel_text}\n\n🌐 {html.escape(news_data['url'])}"
                msg = await send_safe_long_message(context.application.bot, TELEGRAM_CHANNEL_ID, final_text,
                                                   is_channel=True)
                if msg:
                    try:
                        await context.application.bot.pin_chat_message(chat_id=TELEGRAM_CHANNEL_ID,
                                                                       message_id=msg.message_id)
                    except Exception:
                        pass
                await query.edit_message_text("🔥 خبر فوری در کانال منتشر شد.")
                database.mark_url_as_processed(news_data["url"], news_data["title"])

            elif action == "normal":
                final_text = f"{safe_channel_text}\n\n🌐 {html.escape(news_data['url'])}"
                await send_safe_long_message(context.application.bot, TELEGRAM_CHANNEL_ID, final_text, is_channel=True)
                await query.edit_message_text("✅ خبر به صورت عادی در کانال منتشر شد.")
                database.mark_url_as_processed(news_data["url"], news_data["title"])

            elif action == "skip":
                await query.edit_message_text("❌ خبر حذف شد.")
                database.mark_url_as_processed(news_data["url"], news_data["title"])

            del pending_news[news_id]


# ==========================================
# تابع راه‌اندازی و اجرای استاندارد لوپ پایتون
# ==========================================
async def main_async():
    database.init_db()
    loop = asyncio.get_running_loop()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_panel))
    application.add_handler(CallbackQueryHandler(handle_panel_buttons))

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scheduler, 'interval', hours=2, args=[loop, application.bot])
    scheduler.start()

    print("[SUCCESS] ربات با تنظیمات یکپارچه لود شد. در تلگرام دستور /start را بزنید.")

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n[SYSTEM] ربات متوقف شد.")
