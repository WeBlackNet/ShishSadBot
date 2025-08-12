from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import logging
import datetime
import time
import requests


# فعال‌سازی لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8184101432:AAECgR7GKmvbENbI6otRQPnkTSKS4M6wpyk"  # جایگزین کن با توکن واقعی

# ذخیره آخرین پیام‌های کاربران
last_messages = {}
# ذخیره تعداد اخطارهای کاربران
user_warnings = {}  # ساختار: {"chat_id_user_id": count}
# ذخیره وضعیت سکوت کاربران
muted_users = {}  # ساختار: {"chat_id_user_id": expiration_time}

# دیکشنری کلمات کلیدی و توابع مرتبط
KEYWORDS = {
    "کمک": "help_command",
    "راهنما": "help_command",
    "قوانین": "rules",
    "اخرین پیام": "last_message",
    "آخرین پیام": "last_message",
    "اخطار": "warn_user",
    "سابقه": "show_warn_history",
    "ازاد": "unmute_user",
    "آزاد": "unmute_user"
}

# مجوزهای سکوت (فقط خواندن)
# MUTE_PERMISSIONS = ChatPermissions(
#     can_send_messages=False,
#     can_send_media_messages=False,
#     can_send_polls=False,
#     can_send_other_messages=False,
#     can_add_web_page_previews=False,
#     can_change_info=False,
#     can_invite_users=False,
#     can_pin_messages=False
# )

# # مجوزهای عادی (همه مجوزها)
# UNMUTE_PERMISSIONS = ChatPermissions(
#     can_send_messages=True,
#     can_send_media_messages=True,
#     can_send_polls=True,
#     can_send_other_messages=True,
#     can_add_web_page_previews=True,
#     can_change_info=True,
#     can_invite_users=True,
#     can_pin_messages=True
# )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستور /start"""
    user = update.message.from_user
    await update.message.reply_text(
        f"سلام {user.first_name}! من ربات مدیریت گروه تو هستم.\n"
        "دستور /help رو بزن یا «کمک» بنویس تا راهنماییت کنم."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستور کمک"""
    help_text = """
📚 راهنمای دستورات:

دستورات اسلش:
/start - شروع کار با ربات
/help - نمایش راهنما
/rules - نمایش قوانین
/warn - اخطار به کاربر (با ریپلای)
/last - نمایش آخرین پیام کاربر (با ریپلای)

دستورات متنی (بدون اسلش):
«کمک» یا «راهنما» - نمایش این راهنما
«قوانین» - نمایش قوانین گروه
«آخرین پیام» - نمایش آخرین پیام کاربر (با ریپلای)
«اخطار» - اخطار به کاربر (با ریپلای)
«سابقه» - نمایش تعداد اخطارهای کاربر (با ریپلای)
«آزاد» یا «ازاد» - آزاد کردن کاربر از حالت سکوت (با ریپلای)
"""
    await update.message.reply_text(help_text)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستور قوانین"""
    await update.message.reply_text("✅ قوانین گروه:\n1. احترام متقابل\n2. ممنوعیت اسپم\n3. ممنوعیت محتوای غیراخلاقی")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور اخطار به کاربر"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً به یک پیام کاربر ریپلای کنید!")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.message.chat_id
    
    # کلید ذخیره‌سازی در دیکشنری
    user_key = f"{chat_id}_{user.id}"
    
    # افزایش تعداد اخطارها
    current_warnings = user_warnings.get(user_key, 0) + 1
    user_warnings[user_key] = current_warnings
    
    # ارسال پیام اخطار
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚠️ اخطار به کاربر: @{user.username}\n"
             f"تعداد اخطارها: {current_warnings}/3\n"
             "به دلیل نقض قوانین گروه اخطار دریافت کرد!"
    )
    
    # اگر به ۳ اخطار رسید
    if current_warnings >= 3:
        # محاسبه زمان پایان سکوت (۳۰ ثانیه بعد)
        mute_duration = 30  # ثانیه
        expiration_time = time.time() + mute_duration
        
        # اعمال سکوت
        try:
            await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user.id,
                    until_date=datetime.datetime.fromtimestamp(expiration_time),
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                )
            # ذخیره وضعیت سکوت
            muted_users[user_key] = expiration_time
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⛔️ کاربر @{user.username} به دلیل ۳ اخطار به مدت ۳۰ ثانیه سکوت شد!"
            )
        except Exception as e:
            logger.error(f"خطا در سکوت کاربر: {e}")
            await update.message.reply_text("❌ ربات دسترسی لازم برای سکوت کاربر را ندارد!")

async def show_warn_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تعداد اخطارهای کاربر"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً به یک پیام کاربر ریپلای کنید!")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.message.chat_id
    user_key = f"{chat_id}_{user.id}"
    current_warnings = user_warnings.get(user_key, 0)
    
    # بررسی وضعیت سکوت
    mute_status = ""
    if user_key in muted_users:
        remaining = int(muted_users[user_key] - time.time())
        if remaining > 0:
            mute_status = f"\n🔇 وضعیت سکوت: فعال ({remaining} ثانیه باقی مانده)"
        else:
            # حذف سکوت منقضی شده
            del muted_users[user_key]
    
    await update.message.reply_text(
        f"📊 تعداد اخطارهای کاربر @{user.username}: {current_warnings}/3{mute_status}"
    )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آزاد کردن کاربر از حالت سکوت"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً به یک پیام کاربر ریپلای کنید!")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.message.chat_id
    user_key = f"{chat_id}_{user.id}"
    
    # بررسی آیا کاربر سکوت شده است
    if user_key not in muted_users:
        await update.message.reply_text("ℹ️ این کاربر در حال حاضر سکوت نشده است.")
        return
    
    try:
        # برداشتن سکوت
        await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        
        # حذف از لیست سکوت‌ها
        del muted_users[user_key]
        
        # ریست اخطارها
        user_warnings[user_key] = 0
        
        await update.message.reply_text(
            f"✅ کاربر @{user.username} از حالت سکوت خارج شد و اخطارهایش صفر شد."
        )
    except Exception as e:
        logger.error(f"خطا در برداشتن سکوت: {e}")
        await update.message.reply_text("❌ ربات دسترسی لازم برای برداشتن سکوت را ندارد!")

async def last_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آخرین پیام کاربر"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً به یک پیام کاربر ریپلای کنید!")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.message.chat_id
    
    # کلید ذخیره‌سازی در دیکشنری
    user_key = f"{chat_id}_{user.id}"
    
    if user_key in last_messages:
        last_msg = last_messages[user_key]
        await update.message.reply_text(
            f"📝 آخرین پیام کاربر @{user.username}:\n"
            f"🕒 زمان: {last_msg['time']}\n"
            f"💬 متن: {last_msg['text']}"
        )
    else:
        await update.message.reply_text("ℹ️ پیامی از این کاربر ثبت نشده است.")

async def handle_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش کلمات کلیدی"""
    text = update.message.text.strip().lower()
    
    # بررسی وجود کلمه کلیدی در پیام
    for keyword, handler_name in KEYWORDS.items():
        if keyword in text:
            # فراخوانی تابع مربوطه
            handler = globals().get(handler_name)
            if handler:
                await handler(update, context)
                return  # پس از اولین تطابق پردازش را متوقف می‌کنیم

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های عادی و ذخیره آخرین پیام"""
    user = update.message.from_user
    chat_id = update.message.chat_id
    text = update.message.text
    
    # کلید ذخیره‌سازی در دیکشنری
    user_key = f"{chat_id}_{user.id}"
    
    # ذخیره آخرین پیام کاربر
    last_messages[user_key] = {
        'text': text,
        'time': update.message.date.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # مثال: حذف پیام‌های حاوی کلمات غیرمجاز
    forbidden_words = ["اسپم", "تبلیغ", "لینک غیرمجاز"]
    if any(word.lower() in text.lower() for word in forbidden_words):
        await update.message.delete()
        await update.message.reply_text("❌ پیام به دلیل نقض قوانین حذف شد!")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لاگ ارورها"""
    logger.warning(f'خطا: {context.error}')


def main():
    # ساخت اپلیکیشن و پاس دادن توکن
    application = Application.builder().token(TOKEN).build()

    # دستورات اسلش
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("last", last_message))
    
    # پردازش کلمات کلیدی (اولویت بالاتر از پیام‌های عادی)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keywords))
    
    # مدیریت پیام‌های عادی (پس از پردازش کلمات کلیدی)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    # مدیریت خطاها
    application.add_error_handler(error)

    # شروع ربات
    print(">>> ربات فعال شد! CTRL+C برای توقف")
    application.run_polling()

if __name__ == '__main__':
    main()
