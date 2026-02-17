import asyncio
import logging
import os
import requests

from aiogram import Bot, Dispatcher, Router, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "supersecret"
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

dp.include_router(router)


# ================= WEBHOOK =================

async def on_startup(app):
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET
    )
    info = await bot.get_webhook_info()
    print("Webhook info:", info)


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


async def handle(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)

    data = await request.json()

    update = Update.model_validate(data)
    await dp.feed_update(bot, update)

    return web.Response()


def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()


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
        requests.post(GOOGLE_SCRIPT_URL, json=data)
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


# ================= START =================

from aiogram.filters import CommandStart

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

        summary = (
            f"📋 Заявка:\n\n"
            f"Операция: {data.get('operation')}\n"
            f"Модель: {data.get('model')}\n"
            f"Дней: {data.get('days')}\n"
            f"Сумма: {format_price(PRICES[data.get('model')] * int(data.get('days')))} VND"
        )

        save_to_sheets(data)

        await callback.message.edit_text(summary)
        await state.clear()


@router.message()
async def test_handler(message: Message):
    await message.answer("Я работаю")