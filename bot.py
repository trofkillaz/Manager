import asyncio
import logging
import os
import requests

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F

TOKEN = os.getenv("BOT_TOKEN")  # токен из Railway variables
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "supersecret"
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

dp.include_router(router)

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
    await dp.feed_webhook_update(bot, data)
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

def save_to_sheets(data: dict):
    try:
        requests.post(GOOGLE_SCRIPT_URL, json={
            "operation": data.get("operation"),
            "model": data.get("model"),
            "days": data.get("days"),
            "time": data.get("time"),
            "tank": data.get("tank"),
            "clean": data.get("clean"),
            "equipment": ", ".join(data.get("equipment", [])),
            "total_price": data.get("total_price"),
            "payment": data.get("payment"),
            "deposit": data.get("deposit"),
            "currency": data.get("currency"),
            "deposit_payment": data.get("deposit_payment"),
        })
    except Exception as e:
        print("Google Sheets error:", e)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwbiDTYbJSAS_99UTuw-MIJjt3G7t2sDHXYnhqmIme0aSFEJJQGQ5-cz1MKhcq6I7Ou5Q/exec"

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

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать заявку")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await message.answer(
        "Выберите действие:",
        reply_markup=kb
    )


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

    # -------- ОПЕРАЦИЯ --------
    if step == "operation":
        await state.update_data(operation=value)
        await state.set_state(RentWizard.model)

        models = list(PRICES.keys())

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=m, callback_data=f"app|model|{m}")]
                for m in models
            ]
        )

        await callback.message.edit_text("2️⃣ Выберите модель:", reply_markup=kb)

    # -------- МОДЕЛЬ --------
    elif step == "model":
        await state.update_data(model=value)
        await state.set_state(RentWizard.days)

        days = list(range(1, 21))
        rows = [days[i:i+5] for i in range(0, len(days), 5)]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=str(d),
                        callback_data=f"app|days|{d}"
                    )
                    for d in row
                ]
                for row in rows
            ]
        )

        await callback.message.edit_text("3️⃣ Выберите количество дней:", reply_markup=kb)

    # -------- ДНИ --------
    elif step == "days":
        await state.update_data(days=value)
        await state.set_state(RentWizard.time)

        times = [f"{h}:00" for h in range(9, 21)]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t,
                        callback_data=f"app|time|{t}"
                    )
                ] for t in times
            ]
        )

        await callback.message.edit_text("4️⃣ Выберите время:", reply_markup=kb)

    # -------- ВРЕМЯ --------
    elif step == "time":
        await state.update_data(time=value)
        await state.set_state(RentWizard.tank)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=str(i), callback_data=f"app|tank|{i}")
                ] for i in range(1, 7)
            ] + [[
                InlineKeyboardButton(text="Полный", callback_data="app|tank|full")
            ]]
        )

        await callback.message.edit_text("5️⃣ Уровень бака:", reply_markup=kb)

    # -------- БАК --------
    elif step == "tank":
        await state.update_data(tank=value)
        await state.set_state(RentWizard.clean)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="+", callback_data="app|clean|clean"),
                InlineKeyboardButton(text="-", callback_data="app|clean|dirty")
            ]
        ])

        await callback.message.edit_text("6️⃣ Чистота:", reply_markup=kb)

    # -------- ЧИСТОТА --------
    elif step == "clean":
        await state.update_data(clean=value)
        await state.set_state(RentWizard.equipment)

        equipment_items = [
            "1 шлем",
            "2 шлема",
            "2 дождевика",
            "2 плаща",
            "Салфетка",
            "Блокиратор",
            "Багажник",
            "Подушка"
        ]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=e, callback_data=f"app|equipment|{e}")]
                for e in equipment_items
            ] + [[
                InlineKeyboardButton(text="Готово", callback_data="app|confirm|yes")
            ]]
        )

        await callback.message.edit_text(
            "7️⃣ Комплектность (можно выбрать несколько):",
            reply_markup=kb
        )

    # -------- КОМПЛЕКТНОСТЬ --------
    elif step == "equipment":
        data = await state.get_data()
        selected = data.get("equipment", [])

        if value in selected:
            selected.remove(value)
        else:
            selected.append(value)

        await state.update_data(equipment=selected)

        equipment_items = [
            "1 шлем",
            "2 шлема",
            "2 дождевика",
            "2 плаща",
            "Салфетка",
            "Блокиратор",
            "Багажник",
            "Подушка"
        ]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ {e}" if e in selected else e,
                        callback_data=f"app|equipment|{e}"
                    )
                ]
                for e in equipment_items
            ] + [[
                InlineKeyboardButton(text="Готово", callback_data="app|confirm|yes")
            ]]
        )

        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer()

    # -------- ПОДТВЕРЖДЕНИЕ И РАСЧЁТ --------
    elif step == "confirm":
        data = await state.get_data()

        model = data.get("model")
        days = int(data.get("days"))

        total_price = PRICES[model] * days

        await state.update_data(total_price=total_price)
        await state.set_state(RentWizard.payment)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Нал", callback_data="app|payment|cash"),
                InlineKeyboardButton(text="Безнал", callback_data="app|payment|noncash")
            ]
        ])

        await callback.message.edit_text(
    f"💰 Сумма к оплате: {format_price(total_price)} VND\n\n"
    f"Пожалуйста примите оплату:",
    reply_markup=kb
)

    # -------- ОПЛАТА --------
    elif step == "payment":
        await state.update_data(payment=value)
        await state.set_state(RentWizard.deposit)

        deposits = [
            "Паспорт", "50,50", "50", "100", "100,100",
            "2.5М", "5М", "10К", "20К"
        ]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=d, callback_data=f"app|deposit|{d}")]
                for d in deposits
            ]
        )

        await callback.message.edit_text(
            "Примите залог:",
            reply_markup=kb
        )

    # -------- ЗАЛОГ --------
    elif step == "deposit":
        await state.update_data(deposit=value)
        await state.set_state(RentWizard.currency)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="VND", callback_data="app|currency|VND"),
                InlineKeyboardButton(text="$", callback_data="app|currency|USD"),
                InlineKeyboardButton(text="₽", callback_data="app|currency|RUB"),
                InlineKeyboardButton(text="€", callback_data="app|currency|EUR"),
            ]
        ])

        await callback.message.edit_text(
            "Выберите валюту:",
            reply_markup=kb
        )

    # -------- ВАЛЮТА --------
    elif step == "currency":
        await state.update_data(currency=value)
        await state.set_state(RentWizard.deposit_payment)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Нал", callback_data="app|deposit_payment|cash"),
                InlineKeyboardButton(text="Безнал", callback_data="app|deposit_payment|noncash")
            ]
        ])

        await callback.message.edit_text(
            "Форма оплаты залога:",
            reply_markup=kb
        )

    # -------- ФИНАЛ --------
    # -------- ФИНАЛ --------
    elif step == "deposit_payment":
        await state.update_data(deposit_payment=value)

        data = await state.get_data()

        summary = (
            f"📋 Заявка:\n\n"
            f"Операция: {data.get('operation')}\n"
            f"Модель: {data.get('model')}\n"
            f"Количество дней: {data.get('days')}\n"
            f"Время: {data.get('time')}\n"
            f"Бак: {data.get('tank')}\n"
            f"Чистота: {data.get('clean')}\n"
            f"Комплектность: {', '.join(data.get('equipment', []))}\n\n"
            f"Сумма: {format_price(data.get('total_price'))} VND\n"
            f"Оплата: {data.get('payment')}\n"
            f"Залог: {data.get('deposit')} ({data.get('currency')})\n"
            f"Форма залога: {data.get('deposit_payment')}"
        )

        save_to_sheets(data)

        await callback.message.edit_text(summary)
        await state.clear()

