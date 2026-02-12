import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("8430851059:AAFeU-6EGQYjQsv8DqnV0G8gwrOJdcyHjkw")


async def debug_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("CHAT ID:", update.effective_chat.id)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, debug_chat))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()