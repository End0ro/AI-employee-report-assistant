from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from datetime import datetime, timedelta

from bot.config import OWNER_CHAT_ID, TIMEZONE
from bot.models.employee import get_all_employees
from bot.models.report import get_employees_without_report_this_week, get_reports_for_week

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def send_reminder(bot: Bot, is_deadline: bool = False):
    missing = await get_employees_without_report_this_week()

    if not missing:
        return

    if is_deadline:
        # Deadline day: remind employees + notify owner
        for emp in missing:
            try:
                await bot.send_message(
                    chat_id=emp["telegram_id"],
                    text=(
                        "🚨 <b>Сегодня крайний срок сдачи отчёта!</b>\n\n"
                        "Пожалуйста, отправьте отчёт с помощью /report.\n"
                        "Дедлайн: сегодня в 21:00."
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass

        # Notify owner
        if OWNER_CHAT_ID:
            names = "\n".join(
                f"  • {e['full_name']} (@{e['username'] or '—'})" for e in missing
            )
            try:
                await bot.send_message(
                    chat_id=OWNER_CHAT_ID,
                    text=(
                        f"⚠️ <b>Дедлайн сегодня!</b>\n\n"
                        f"Ещё не сдали отчёт ({len(missing)}):\n{names}"
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass
    else:
        # Pre-deadline reminder to employees only
        for emp in missing:
            try:
                await bot.send_message(
                    chat_id=emp["telegram_id"],
                    text=(
                        "⏰ <b>Напоминание!</b>\n\n"
                        "Не забудьте сдать еженедельный отчёт.\n"
                        "Дедлайн: суббота, 21:00.\n\n"
                        "Отправьте отчёт: /report"
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass


async def check_missed_deadline(bot: Bot):
    """Called after the deadline passes. Notifies owner about missing reports."""
    missing = await get_employees_without_report_this_week()

    if not missing and OWNER_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text="🎉 <b>Все сотрудники сдали отчёт на этой неделе!</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    if missing and OWNER_CHAT_ID:
        names = "\n".join(
            f"  • {e['full_name']} (@{e['username'] or '—'})" for e in missing
        )
        try:
            await bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=(
                    f"🚫 <b>Дедлайн прошёл!</b>\n\n"
                    f"Не сдали отчёт ({len(missing)}):\n{names}\n\n"
                    f"Эти сотрудники пропустили дедлайн."
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

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


async def send_monday_summary(bot: Bot):
    """Monday morning: send owner a summary of last week's reports."""
    if not OWNER_CHAT_ID:
        return

    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_week_start = last_monday.strftime("%Y-%m-%d")

    all_employees = await get_all_employees()
    reports = await get_reports_for_week(last_week_start)

    submitted_ids = {r["employee_id"] for r in reports}
    submitted = [e for e in all_employees if e["id"] in submitted_ids]
    not_submitted = [e for e in all_employees if e["id"] not in submitted_ids]

    lines = [
        f"📅 <b>Новая неделя началась!</b>\n",
        f"Итоги прошлой недели ({last_week_start}):\n",
        f"📊 Сдали отчёт: {len(submitted)}/{len(all_employees)}\n",
    ]

    if submitted:
        lines.append("✅ <b>Сдали:</b>")
        for e in submitted:
            lines.append(f"  • {e['full_name']} (@{e['username'] or '—'})")

    if not_submitted:
        lines.append("\n❌ <b>Не сдали:</b>")
        for e in not_submitted:
            lines.append(f"  • {e['full_name']} (@{e['username'] or '—'})")

    if not all_employees:
        lines.append("Нет зарегистрированных сотрудников.")

    try:
        await bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text="\n".join(lines),
            parse_mode="HTML",
        )
    except Exception:
        pass


def setup_scheduler(bot: Bot):
    # Thursday 21:00 MSK — 2 days before deadline
    scheduler.add_job(
        send_reminder,
        CronTrigger(day_of_week="thu", hour=21, minute=0, timezone=TIMEZONE),
        args=[bot, False],
        id="reminder_thursday",
        replace_existing=True,
    )

    # Friday 21:00 MSK — 1 day before deadline
    scheduler.add_job(
        send_reminder,
        CronTrigger(day_of_week="fri", hour=21, minute=0, timezone=TIMEZONE),
        args=[bot, False],
        id="reminder_friday",
        replace_existing=True,
    )

    # Saturday 21:00 MSK — deadline day
    scheduler.add_job(
        send_reminder,
        CronTrigger(day_of_week="sat", hour=21, minute=0, timezone=TIMEZONE),
        args=[bot, True],
        id="reminder_deadline",
        replace_existing=True,
    )

    # Saturday 23:00 MSK — check missed deadlines (2 hours after deadline)
    scheduler.add_job(
        check_missed_deadline,
        CronTrigger(day_of_week="sat", hour=23, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="check_missed",
        replace_existing=True,
    )

    # Monday 9:00 MSK — weekly summary to owner
    scheduler.add_job(
        send_monday_summary,
        CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="monday_summary",
        replace_existing=True,
    )

    scheduler.start()
