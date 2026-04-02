from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

from bot.config import OWNER_CHAT_ID
from bot.models.employee import get_all_employees
from bot.models.report import get_reports_for_week, get_employees_without_report_this_week
from bot.utils.formatters import format_report_summary, format_employee_list

router = Router()


def is_owner(message: Message) -> bool:
    return message.from_user.id == OWNER_CHAT_ID


@router.message(Command("reports"))
async def cmd_reports(message: Message):
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    reports = await get_reports_for_week()
    await message.answer(format_report_summary(reports), parse_mode="HTML")


@router.message(Command("employees"))
async def cmd_employees(message: Message):
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    employees = await get_all_employees()
    await message.answer(format_employee_list(employees), parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message):
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    missing = await get_employees_without_report_this_week()
    all_employees = await get_all_employees()
    submitted_count = len(all_employees) - len(missing)

    lines = [
        f"📊 <b>Статус отчётов за неделю</b>\n",
        f"✅ Сдали отчёт: {submitted_count}/{len(all_employees)}",
    ]

    if missing:
        lines.append(f"\n❌ <b>Не сдали отчёт:</b>")
        for e in missing:
            lines.append(f"  • {e['full_name']} (@{e['username'] or '—'})")
    else:
        lines.append("\n🎉 Все сотрудники сдали отчёт!")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("testreminder"))
async def cmd_test_reminder(message: Message, bot: Bot):
    """Simulates the full reminder cycle: 3 reminders + missed deadline report to owner."""
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    missing = await get_employees_without_report_this_week()

    if not missing:
        await message.answer("✅ Все сотрудники уже сдали отчёт. Некому отправлять напоминание.")
        return

    await message.answer("🧪 <b>Запуск полного цикла напоминаний...</b>", parse_mode="HTML")

    # --- Reminder 1: Friday (2 days before) ---
    sent = 0
    for emp in missing:
        try:
            await bot.send_message(
                chat_id=emp["telegram_id"],
                text=(
                    "⏰ <b>Напоминание!</b>\n\n"
                    "Не забудьте сдать еженедельный отчёт.\n"
                    "Дедлайн: воскресенье, 18:00.\n"
                    "Осталось 2 дня.\n\n"
                    "Отправьте отчёт: /report"
                ),
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass
    await message.answer(f"1️⃣ Напоминание (за 2 дня) отправлено: {sent}/{len(missing)}")

    await asyncio.sleep(10)

    # --- Reminder 2: Saturday (1 day before) ---
    missing = await get_employees_without_report_this_week()
    if not missing:
        await message.answer("✅ Все сотрудники сдали отчёт! Цикл завершён.")
        return

    sent = 0
    for emp in missing:
        try:
            await bot.send_message(
                chat_id=emp["telegram_id"],
                text=(
                    "⏰ <b>Напоминание!</b>\n\n"
                    "Не забудьте сдать еженедельный отчёт.\n"
                    "Дедлайн: воскресенье, 18:00.\n"
                    "Остался 1 день.\n\n"
                    "Отправьте отчёт: /report"
                ),
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass
    await message.answer(f"2️⃣ Напоминание (за 1 день) отправлено: {sent}/{len(missing)}")

    await asyncio.sleep(10)

    # --- Reminder 3: Sunday (deadline day) ---
    missing = await get_employees_without_report_this_week()
    if not missing:
        await message.answer("✅ Все сотрудники сдали отчёт! Цикл завершён.")
        return

    sent = 0
    for emp in missing:
        try:
            await bot.send_message(
                chat_id=emp["telegram_id"],
                text=(
                    "🚨 <b>Сегодня крайний срок сдачи отчёта!</b>\n\n"
                    "Пожалуйста, отправьте отчёт с помощью /report.\n"
                    "Дедлайн: сегодня в 18:00."
                ),
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass
    await message.answer(f"3️⃣ Напоминание (дедлайн!) отправлено: {sent}/{len(missing)}")

    await asyncio.sleep(10)

    # --- Missed deadline: auto-notify owner ---
    missing = await get_employees_without_report_this_week()
    if not missing:
        await message.answer("🎉 <b>Все сотрудники сдали отчёт на этой неделе!</b>", parse_mode="HTML")
        return

    names = "\n".join(
        f"  • {e['full_name']} (@{e['username'] or '—'})" for e in missing
    )
    await bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            f"🚫 <b>Дедлайн прошёл!</b>\n\n"
            f"Не сдали отчёт ({len(missing)}):\n{names}\n\n"
            f"Эти сотрудники пропустили дедлайн."
        ),
        parse_mode="HTML",
    )

    for emp in missing:
        try:
            await bot.send_message(
                chat_id=emp["telegram_id"],
                text=(
                    "❗ <b>Вы пропустили дедлайн!</b>\n\n"
                    "Отчёт за эту неделю не был сдан вовремя.\n"
                    "Пожалуйста, отправьте его как можно скорее: /report"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await message.answer("✅ <b>Тест завершён.</b> Полный цикл напоминаний выполнен.", parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — регистрация в боте\n"
        "/report — отправить еженедельный отчёт\n"
        "/cancel — отменить текущее действие\n"
        "/help — список команд\n"
    )

    if is_owner(message):
        text += (
            "\n👑 <b>Команды владельца:</b>\n\n"
            "/reports — все отчёты за неделю\n"
            "/employees — список сотрудников\n"
            "/status — кто сдал, кто нет\n"
            "/testreminder — полный цикл: 3 напоминания + отчёт владельцу\n"
        )

    await message.answer(text, parse_mode="HTML")
