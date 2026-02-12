from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "8430851059:AAFeU-6EGQYjQsv8DqnV0G8gwrOJdcyHjkw"

async def debug_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("CHAT ID:", update.effective_chat.id)
    print("MESSAGE:", update.message.text)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Ловим ВСЕ сообщения
    app.add_handler(MessageHandler(filters.ALL, debug_chat))

    print("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())