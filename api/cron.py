"""Vercel Cron Job handler for deadline reminders.

Vercel calls this endpoint on a schedule defined in vercel.json.
It checks which employees haven't submitted reports and sends reminders.
"""

import json
import os
from http.server import BaseHTTPRequestHandler
import asyncio
from datetime import datetime
import pytz

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, OWNER_CHAT_ID, TIMEZONE
from bot.models.database import init_db
from bot.models.report import get_employees_without_report_this_week

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


async def send_reminders():
    await init_db()

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    day = now.strftime("%A").lower()

    missing = await get_employees_without_report_this_week()

    if not missing:
        return "no_missing"

    is_deadline = day == "sunday"

    for emp in missing:
        try:
            if is_deadline:
                text = (
                    "🚨 <b>Сегодня крайний срок сдачи отчёта!</b>\n\n"
                    "Пожалуйста, отправьте отчёт с помощью /report.\n"
                    "Дедлайн: сегодня в 18:00."
                )
            else:
                text = (
                    "⏰ <b>Напоминание!</b>\n\n"
                    "Не забудьте сдать еженедельный отчёт.\n"
                    "Дедлайн: воскресенье, 18:00.\n\n"
                    "Отправьте отчёт: /report"
                )
            await bot.send_message(chat_id=emp["telegram_id"], text=text, parse_mode="HTML")
        except Exception:
            pass

    # Notify owner on deadline day
    if is_deadline and OWNER_CHAT_ID:
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

    await bot.session.close()
    return "reminders_sent"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verify cron secret to prevent unauthorized calls
        cron_secret = os.getenv("CRON_SECRET", "")
        auth_header = self.headers.get("Authorization", "")

        if cron_secret and f"Bearer {cron_secret}" != auth_header:
            self.send_response(401)
            self.end_headers()
            return

        result = asyncio.run(send_reminders())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"result": result}).encode())
