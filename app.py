from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest  # Import جدید

# تنظیمات پروکسی و توکن
TOKEN = "8184101432:AAECgR7GKmvbENbI6otRQPnkTSKS4M6wpyk"  # جایگزین کن با توکن ربات خودت
PROXY_URL = "https://t.me/proxy?server=178.130.42.116&port=443&secret=eed77db43ee3721f0fcb40a4ff63b5cd276D656469612E737465616D706F77657265642E636F6D"  # آدرس پروکسی تو (با پروتکل صحیح)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.message.from_user
    await update.message.reply_text(
        f'سلام {user.first_name}! من با موفقیت از طریق پروکسی وصل شدم. 😎\n'
        'هر پیامی بفرستی برات تکرارش می‌کنم.'
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تکرار پیام کاربر"""
    user_text = update.message.text
    await update.message.reply_text(f'دریافت شد: "{user_text}"')

def main():
    # ساخت درخواست با پروکسی
    request = HTTPXRequest(proxy_url=PROXY_URL)
    
    # ساخت Application با تنظیمات پروکسی
    application = Application.builder() \
        .token(TOKEN) \
        .request(request) \
        .build()

    # افزودن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # شروع ربات
    print(f"🤖 ربات با پروکسی {PROXY_URL} در حال اجراست...")
    application.run_polling()

if __name__ == "__main__":
    main()