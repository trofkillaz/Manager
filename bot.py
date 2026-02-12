import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

# Вставь сюда токен напрямую для теста
TOKEN = "8430851059:AAFeU-6EGQYjQsv8DqnV0G8gwrOJdcyHjkw"

logging.basicConfig(level=logging.INFO)


# ============================
# DEBUG — вывод ID чатов
# ============================
async def debug_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    print("------------")
    print("CHAT TITLE:", chat.title)
    print("CHAT ID:", chat.id)
    print("CHAT TYPE:", chat.type)
    print("FROM USER:", user.username if user else "Unknown")
    print("------------")


# ============================
# Запуск бота
# ============================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Ловим вообще всё
    app.add_handler(MessageHandler(filters.ALL, debug_chat))

    print("Manager bot started...")
    app.run_polling()