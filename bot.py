import logging
import os
import requests

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart


# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
WEBHOOK_URL = "https://manager-production-17b0.up.railway.app/webhook"

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


# ================= WEBHOOK HANDLERS =================

async def on_startup(app):
    """Setup webhook on startup"""
    print(f"🚀 Starting bot...")
    print(f"Setting webhook to: {WEBHOOK_URL}")
    
    try:
        # Delete old webhook to avoid conflicts
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Set new webhook
        await bot.set_webhook(
            WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET
        )
        
        # Verify webhook
        info = await bot.get_webhook_info()
        print(f"✅ Webhook set successfully!")
        print(f"Webhook info: {info}")
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        raise


async def on_shutdown(app):
    """Cleanup on shutdown"""
    print("🛑 Shutting down bot...")
    try:
        await bot.delete_webhook()
        await bot.session.close()
        print("✅ Bot shutdown complete")
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")


async def handle(request):
    """Handle incoming webhook updates"""
    # Verify secret token
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        print("❌ Invalid webhook secret token")
        return web.Response(status=403)
    
    try:
        data = await request.json()
        update = Update.model_validate(data)
        
        # Process update using aiogram 3 webhook method
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        print(f"❌ Error processing update: {e}")
    
    return web.Response()


# ================= PRICES =================

PRICES = {
    "Honda Lead": 200000,
    "Honda PCX": 250000,
    "Yamaha NVX": 250000,
    "Honda Vision": 180000,
    "Honda Airblade": 220000
}


def format_price(value: int) -> str:
    return f"{value:,}".replace(",", " ")


GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwbiDTYbJSAS_99UTuw-MIJjt3G7t2sDHXYnhqmIme0aSFEJJQGQ5-cz1MKhcq6I7Ou5Q/exec"

def save_to_sheets(data: dict):
    try:
        requests.post(GOOGLE_SCRIPT_URL, json=data, timeout=5)
    except Exception as e:
        print("Google Sheets error:", e)


# ================= STATES =================

class RentWizard(StatesGroup):
    operation = State()
    model = State()
    days = State()
    time = State()
    tank = State()
    clean = State()
    equipment = State()
    payment = State()
    deposit = State()
    currency = State()
    deposit_payment = State()


# ================= HANDLERS =================

@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Создать заявку")]],
        resize_keyboard=True
    )
    
    await message.answer("Выберите действие:", reply_markup=kb)


@router.message(F.text == "Создать заявку")
async def start_application(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RentWizard.operation)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Приход", callback_data="app|operation|income"),
            InlineKeyboardButton(text="Расход", callback_data="app|operation|expense"),
        ]
    ])
    
    await message.answer("1️⃣ Выберите операцию:", reply_markup=kb)


# ================= CALLBACK FLOW =================

@router.callback_query(F.data.startswith("app|"))
async def application_flow(callback: CallbackQuery, state: FSMContext):
    _, step, value = callback.data.split("|")
    
    if step == "operation":
        await state.update_data(operation=value)
        await state.set_state(RentWizard.model)
        
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=m, callback_data=f"app|model|{m}")]
                for m in PRICES.keys()
            ]
        )
        
        await callback.message.edit_text("2️⃣ Выберите модель:", reply_markup=kb)
    
    elif step == "model":
        await state.update_data(model=value)
        await state.set_state(RentWizard.days)
        
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=str(d), callback_data=f"app|days|{d}")]
                for d in range(1, 21)
            ]
        )
        
        await callback.message.edit_text("3️⃣ Выберите количество дней:", reply_markup=kb)
    
    elif step == "days":
        await state.update_data(days=value)
        await state.set_state(RentWizard.time)
        
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{h}:00", callback_data=f"app|time|{h}:00")]
                for h in range(9, 21)
            ]
        )
        
        await callback.message.edit_text("4️⃣ Выберите время:", reply_markup=kb)
    
    elif step == "time":
        await state.update_data(time=value)
        await state.set_state(RentWizard.tank)
        
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=str(i), callback_data=f"app|tank|{i}")]
                for i in range(1, 7)
            ]
        )
        
        await callback.message.edit_text("5️⃣ Уровень бака:", reply_markup=kb)
    
    elif step == "deposit_payment":
        await state.update_data(deposit_payment=value)
        data = await state.get_data()
        
        total = PRICES[data.get('model')] * int(data.get('days'))
        
        summary = (
            f"📋 Заявка:\n\n"
            f"Операция: {data.get('operation')}\n"
            f"Модель: {data.get('model')}\n"
            f"Дней: {data.get('days')}\n"
            f"Сумма: {format_price(total)} VND"
        )
        
        save_to_sheets(data)
        
        await callback.message.edit_text(summary)
        await state.clear()


# ================= FALLBACK =================

@router.message()
async def fallback(message: Message):
    await message.answer("Я работаю")


# ================= SERVER SETUP =================

def main():
    """Setup and run aiohttp web application"""
    app = web.Application()
    
    # Add webhook handler
    app.router.add_post(WEBHOOK_PATH, handle)
    
    # Setup startup and shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Get port from environment
    port = int(os.getenv("PORT", 8080))
    
    print(f"🌐 Starting aiohttp server on port {port}...")
    
    # Run app
    web.run_app(
        app,
        host="0.0.0.0",
        port=port
    )


# ================= ENTRY POINT =================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()