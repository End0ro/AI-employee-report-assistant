"""One-time helper to set the Telegram webhook URL.

Call this endpoint once after deployment:
  GET https://your-app.vercel.app/api/set_webhook
"""

import json
import os
from http.server import BaseHTTPRequestHandler
import asyncio

from aiogram import Bot

from bot.config import BOT_TOKEN


async def set_webhook():
    bot = Bot(token=BOT_TOKEN)
    vercel_url = os.getenv("VERCEL_URL", "")

    if not vercel_url:
        return {"error": "VERCEL_URL not set"}

    webhook_url = f"https://{vercel_url}/api/webhook"
    await bot.set_webhook(webhook_url)
    await bot.session.close()
    return {"webhook_url": webhook_url, "status": "ok"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = asyncio.run(set_webhook())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
