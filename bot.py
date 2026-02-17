import asyncio
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart


# ================= TOKEN =================

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# ================= STATES =================

class RentWizard(StatesGroup):
    operation = State()
    model = State()
    package = State()
    days = State()
    time = State()
    tank = State()
    clean = State()
    equipment = State()


# ================= START =================

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart


@router.message(CommandStart())
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

        models = [
            "Honda Lead",
            "Honda PCX",
            "Yamaha NVX",
            "Honda Vision",
            "Honda Airblade"
        ]

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
        await state.set_state(RentWizard.package)

        packages = [1, 3, 7, 14]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{p} дней",
                        callback_data=f"app|package|{p}"
                    )
                ] for p in packages
            ]
        )

        await callback.message.edit_text("3️⃣ Выберите пакет:", reply_markup=kb)

    # -------- ПАКЕТ --------
    elif step == "package":
        await state.update_data(package=value)
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

        await callback.message.edit_text("4️⃣ Выберите количество дней:", reply_markup=kb)

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

        await callback.message.edit_text("5️⃣ Выберите время:", reply_markup=kb)

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

        await callback.message.edit_text("6️⃣ Уровень бака:", reply_markup=kb)

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

        await callback.message.edit_text("7️⃣ Чистота:", reply_markup=kb)

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
            "8️⃣ Комплектность (можно выбрать несколько):",
            reply_markup=kb
        )

    # -------- КОМПЛЕКТНОСТЬ --------
    elif step == "equipment":
    data = await state.get_data()
    selected = data.get("equipment", [])

    # toggle логика
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

    # пересобираем клавиатуру с галочками
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

    # -------- ПОДТВЕРЖДЕНИЕ --------
    elif step == "confirm":
        data = await state.get_data()

        summary = (
            f"📋 Заявка:\n\n"
            f"Операция: {data.get('operation')}\n"
            f"Модель: {data.get('model')}\n"
            f"Пакет: {data.get('package')} дней\n"
            f"Количество дней: {data.get('days')}\n"
            f"Время: {data.get('time')}\n"
            f"Бак: {data.get('tank')}\n"
            f"Чистота: {data.get('clean')}\n"
            f"Комплектность: {', '.join(data.get('equipment', []))}"
        )

        await callback.message.edit_text(summary)
        await state.clear()

    await callback.answer()


# ================= REGISTER ROUTER =================

dp.include_router(router)


# ================= MAIN =================

async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())