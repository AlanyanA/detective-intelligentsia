from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from detective_bot.engine.exceptions import InvalidChoiceError, SceneAccessDeniedError, StoryEngineError
from detective_bot.services.game_service import GameService
from detective_bot.services.story_catalog import StoryCatalog
from detective_bot.telegram.callbacks import CONTINUE_CALLBACK, RESTART_CALLBACK, STORIES_CALLBACK
from detective_bot.telegram.keyboards import main_menu_keyboard, story_list_keyboard
from detective_bot.telegram.rendering import TelegramSceneSender

logger = logging.getLogger(__name__)


def build_router(game_service: GameService, catalog: StoryCatalog, sender: TelegramSceneSender) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def start(message: Message) -> None:
        states = await game_service.list_user_states(message.from_user.id)
        await message.answer(
            "Choose a case or continue your latest investigation.",
            reply_markup=main_menu_keyboard(has_continue=bool(states)),
        )

    @router.message(Command("stories"))
    async def stories_command(message: Message) -> None:
        await _send_story_list(message)

    @router.message(Command("continue"))
    async def continue_command(message: Message) -> None:
        await _continue(message)

    @router.message(Command("restart"))
    async def restart_hint(message: Message) -> None:
        await message.answer("Open the current ending or choose a story, then use Restart.")

    @router.callback_query(F.data == STORIES_CALLBACK)
    async def stories_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await _send_story_list(callback.message)

    @router.callback_query(F.data == CONTINUE_CALLBACK)
    async def continue_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await _continue(callback.message)

    @router.callback_query(F.data.startswith("s:"))
    async def story_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.from_user:
            return
        story_id = callback.data.split(":", maxsplit=1)[1]
        view = await game_service.continue_story(callback.from_user.id, story_id)
        if view is None:
            view = await game_service.start_story(callback.from_user.id, story_id)
        await sender.answer_scene(callback.message, view.rendered)

    @router.callback_query(F.data == RESTART_CALLBACK)
    async def restart_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.from_user:
            return
        view = await game_service.restart_latest(callback.from_user.id)
        if view is None:
            await callback.message.answer("No saved investigation yet. Choose a case first.")
            return
        await sender.answer_scene(callback.message, view.rendered)

    @router.callback_query(F.data.startswith("c:"))
    async def choice_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.from_user:
            return
        choice_id = callback.data.split(":", maxsplit=1)[1]
        try:
            view = await game_service.choose_latest(callback.from_user.id, choice_id)
        except (InvalidChoiceError, SceneAccessDeniedError):
            await callback.message.answer("That path is no longer available. Use /continue.")
            return
        except StoryEngineError:
            logger.exception("Story engine failure")
            await callback.message.answer("The case file could not be opened. Try again later.")
            return
        await sender.answer_scene(callback.message, view.rendered)

    async def _send_story_list(message: Message) -> None:
        stories = catalog.list_stories()
        if not stories:
            await message.answer("No cases are available yet.")
            return
        await message.answer("Available cases:", reply_markup=story_list_keyboard(stories))

    async def _continue(message: Message) -> None:
        view = await game_service.continue_latest(message.from_user.id)
        if view is None:
            await message.answer("No saved investigation yet. Choose a case first.", reply_markup=story_list_keyboard(catalog.list_stories()))
            return
        await sender.answer_scene(message, view.rendered)

    return router
