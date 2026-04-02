import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.models.database import init_db
from bot.handlers import start, report, admin
from bot.services.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set! Create a .env file with your bot token.")
        return

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register handlers
    dp.include_router(start.router)
    dp.include_router(report.router)
    dp.include_router(admin.router)

    # Setup scheduled reminders
    setup_scheduler(bot)
    logger.info("Scheduler started")

    # Delete any old webhook (e.g. from Vercel) so polling works
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared, starting polling...")

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
