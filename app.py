from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os

TOKEN = os.environ.get('8184101432:AAECgR7GKmvbENbI6otRQPnkTSKS4M6wpyk')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ ربات با موفقیت روی سرور اجرا شد!')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'شما گفتید: {update.message.text}')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("🤖 ربات در حال اجرا...")
    app.run_polling()

if __name__ == "__main__":
    main()
