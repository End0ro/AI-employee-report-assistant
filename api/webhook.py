import json
import os
from http.server import BaseHTTPRequestHandler
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from bot.config import BOT_TOKEN
from bot.models.database import init_db
from bot.handlers import start, report, admin

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Register handlers
dp.include_router(start.router)
dp.include_router(report.router)
dp.include_router(admin.router)


async def process_update(update_data: dict):
    await init_db()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        update_data = json.loads(body.decode("utf-8"))

        asyncio.run(process_update(update_data))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Bot is running"}).encode())
