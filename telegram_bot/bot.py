import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from telegram_bot.config import TELEGRAM_BOT_TOKEN, DATABASE_URL
from telegram_bot.handlers import start #, recommend
from db_interaction.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    repository = PublicationRepository(DATABASE_URL)

    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp["repository"] = repository

    dp.include_router(start.router)
    #dp.include_router(recommend.router)

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())