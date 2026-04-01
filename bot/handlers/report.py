from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import OWNER_CHAT_ID
from bot.models.employee import get_employee_by_telegram_id
from bot.models.report import save_report, has_report_this_week
from bot.utils.formatters import format_report
from bot.models.report import get_current_week_start

router = Router()

CONFIRM_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


class ReportForm(StatesGroup):
    ads_posted = State()
    views = State()
    reach_outs = State()
    favorites = State()
    ad_spend = State()
    confirm = State()


@router.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    employee = await get_employee_by_telegram_id(message.from_user.id)
    if not employee:
        await message.answer(
            "❌ Вы не зарегистрированы. Нажмите /start для регистрации."
        )
        return

    already_submitted = await has_report_this_week(employee["id"])
    if already_submitted:
        await message.answer(
            "ℹ️ Вы уже отправили отчёт на этой неделе.\n"
            "Новый отчёт заменит предыдущий.",
        )

    await state.update_data(employee_id=employee["id"], full_name=employee["full_name"],
                            username=employee["username"], telegram_id=employee["telegram_id"])
    await message.answer(
        "📋 <b>Заполнение отчёта</b>\n\n"
        "Шаг 1/5: Сколько объявлений было <b>размещено</b>?",
        parse_mode="HTML",
    )
    await state.set_state(ReportForm.ads_posted)


@router.message(ReportForm.ads_posted)
async def process_ads_posted(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Введите целое число. Попробуйте ещё раз:")
        return

    await state.update_data(ads_posted=int(message.text.strip()))
    await message.answer(
        "Шаг 2/5: Сколько <b>просмотров</b> получили объявления?",
        parse_mode="HTML",
    )
    await state.set_state(ReportForm.views)


@router.message(ReportForm.views)
async def process_views(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Введите целое число. Попробуйте ещё раз:")
        return

    await state.update_data(views=int(message.text.strip()))
    await message.answer(
        "Шаг 3/5: Сколько людей <b>обратились</b> (написали/позвонили)?",
        parse_mode="HTML",
    )
    await state.set_state(ReportForm.reach_outs)


@router.message(ReportForm.reach_outs)
async def process_reach_outs(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Введите целое число. Попробуйте ещё раз:")
        return

    await state.update_data(reach_outs=int(message.text.strip()))
    await message.answer(
        "Шаг 4/5: Сколько раз объявления добавили в <b>избранное</b>?",
        parse_mode="HTML",
    )
    await state.set_state(ReportForm.favorites)


@router.message(ReportForm.favorites)
async def process_favorites(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Введите целое число. Попробуйте ещё раз:")
        return

    await state.update_data(favorites=int(message.text.strip()))
    await message.answer(
        "Шаг 5/5: Какая сумма была потрачена на <b>продвижение</b> (₽)?\n"
        "Введите число (например: 1500 или 1500.50):",
        parse_mode="HTML",
    )
    await state.set_state(ReportForm.ad_spend)


@router.message(ReportForm.ad_spend)
async def process_ad_spend(message: Message, state: FSMContext):
    try:
        ad_spend = float(message.text.strip().replace(",", "."))
        if ad_spend < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 1500 или 1500.50):")
        return

    await state.update_data(ad_spend=ad_spend)
    data = await state.get_data()

    summary = (
        "📊 <b>Проверьте ваш отчёт:</b>\n\n"
        f"📌 Размещено объявлений: <b>{data['ads_posted']}</b>\n"
        f"👁 Просмотры: <b>{data['views']}</b>\n"
        f"📩 Обращения: <b>{data['reach_outs']}</b>\n"
        f"⭐️ В избранном: <b>{data['favorites']}</b>\n"
        f"💰 Расходы на продвижение: <b>{data['ad_spend']:.2f} ₽</b>\n\n"
        "Всё верно?"
    )
    await message.answer(summary, parse_mode="HTML", reply_markup=CONFIRM_KB)
    await state.set_state(ReportForm.confirm)


@router.message(ReportForm.confirm)
async def process_confirm(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отменить":
        await message.answer(
            "🚫 Отчёт отменён. Используйте /report чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    if message.text != "✅ Подтвердить":
        await message.answer("Нажмите одну из кнопок ниже:", reply_markup=CONFIRM_KB)
        return

    data = await state.get_data()

    report_id = await save_report(
        employee_id=data["employee_id"],
        ads_posted=data["ads_posted"],
        views=data["views"],
        reach_outs=data["reach_outs"],
        favorites=data["favorites"],
        ad_spend=data["ad_spend"],
    )

    await message.answer(
        "✅ Отчёт успешно отправлен! Спасибо.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Forward report to owner
    from datetime import datetime
    report_data = {
        "full_name": data["full_name"],
        "username": data.get("username"),
        "week_start": get_current_week_start(),
        "ads_posted": data["ads_posted"],
        "views": data["views"],
        "reach_outs": data["reach_outs"],
        "favorites": data["favorites"],
        "ad_spend": data["ad_spend"],
        "submitted_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    if OWNER_CHAT_ID:
        await bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"📥 <b>Новый отчёт!</b>\n\n{format_report(report_data)}",
            parse_mode="HTML",
        )

    await state.clear()
