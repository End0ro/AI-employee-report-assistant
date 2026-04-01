from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.models.employee import create_employee, get_employee_by_telegram_id

router = Router()


class Registration(StatesGroup):
    waiting_for_name = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    employee = await get_employee_by_telegram_id(message.from_user.id)

    if employee:
        await message.answer(
            f"👋 С возвращением, <b>{employee['full_name']}</b>!\n\n"
            f"Используйте /report чтобы отправить отчёт.\n"
            f"Используйте /help чтобы увидеть все команды.",
            parse_mode="HTML",
        )
        return

    await message.answer(
        "👋 Добро пожаловать! Я бот для сбора отчётов по Avito.\n\n"
        "Для начала, напишите ваше <b>имя и фамилию</b>:",
        parse_mode="HTML",
    )
    await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text.strip()

    if len(full_name) < 2:
        await message.answer("❌ Имя слишком короткое. Попробуйте ещё раз:")
        return

    await create_employee(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=full_name,
    )

    await message.answer(
        f"✅ Регистрация завершена, <b>{full_name}</b>!\n\n"
        f"📋 Команды:\n"
        f"/report — отправить отчёт\n"
        f"/help — список команд",
        parse_mode="HTML",
    )
    await state.clear()
