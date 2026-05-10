from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from detective_bot.config import get_settings
from detective_bot.db import Database
from detective_bot.engine import ConditionEvaluator, SceneRenderer, StateMutator, StoryLoader
from detective_bot.services import GameService, StoryCatalog
from detective_bot.telegram import TelegramSceneSender, build_router


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required.")

    database = Database(settings.sqlite_path)
    await database.initialize()

    loader = StoryLoader(settings.stories_path)
    renderer = SceneRenderer(ConditionEvaluator(), StateMutator())
    game_service = GameService(database, loader, renderer)
    catalog = StoryCatalog(loader)
    sender = TelegramSceneSender(settings.stories_path)

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(game_service, catalog, sender))
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
