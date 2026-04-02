from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

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
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    missing = await get_employees_without_report_this_week()

    if not missing:
        await message.answer("✅ Все сотрудники уже сдали отчёт. Некому отправлять напоминание.")
        return

    sent = 0
    for emp in missing:
        try:
            await bot.send_message(
                chat_id=emp["telegram_id"],
                text=(
                    "⏰ <b>Напоминание!</b>\n\n"
                    "Не забудьте сдать еженедельный отчёт.\n"
                    "Дедлайн: воскресенье, 18:00.\n\n"
                    "Отправьте отчёт: /report"
                ),
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            pass

    await message.answer(
        f"📨 Напоминание отправлено: {sent}/{len(missing)} сотрудникам.",
    )


@router.message(Command("testmissed"))
async def cmd_test_missed(message: Message, bot: Bot):
    if not is_owner(message):
        await message.answer("❌ Эта команда доступна только владельцу.")
        return

    missing = await get_employees_without_report_this_week()

    if not missing:
        await message.answer("🎉 <b>Все сотрудники сдали отчёт на этой неделе!</b>", parse_mode="HTML")
        return

    names = "\n".join(
        f"  • {e['full_name']} (@{e['username'] or '—'})" for e in missing
    )
    await message.answer(
        f"🚫 <b>Не сдали отчёт ({len(missing)}):</b>\n{names}\n\n"
        f"Эти сотрудники пропустили дедлайн.",
        parse_mode="HTML",
    )

    # Also notify employees who missed
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


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — регистрация в боте\n"
        "/report — отправить еженедельный отчёт\n"
        "/help — список команд\n"
    )

    if is_owner(message):
        text += (
            "\n👑 <b>Команды владельца:</b>\n\n"
            "/reports — все отчёты за неделю\n"
            "/employees — список сотрудников\n"
            "/status — кто сдал, кто нет\n"
            "/testreminder — отправить напоминание сейчас\n"
            "/testmissed — проверить пропущенные дедлайны\n"
        )

    await message.answer(text, parse_mode="HTML")
