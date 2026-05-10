from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from detective_bot.models.rendered import RenderedChoice
from detective_bot.services.story_catalog import StorySummary
from detective_bot.telegram.callbacks import (
    CONTINUE_CALLBACK,
    RESTART_CALLBACK,
    STORIES_CALLBACK,
    choice_callback,
    story_callback,
)


def story_list_keyboard(stories: list[StorySummary]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for story in stories:
        builder.button(text=story.title, callback_data=story_callback(story.id))
    builder.adjust(1)
    return builder.as_markup()


def scene_choices_keyboard(choices: tuple[RenderedChoice, ...], is_ending: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for choice in choices:
        builder.button(text=choice.text, callback_data=choice_callback(choice.id))
    if is_ending:
        builder.button(text="Restart", callback_data=RESTART_CALLBACK)
        builder.button(text="Stories", callback_data=STORIES_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(has_continue: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_continue:
        builder.button(text="Continue", callback_data=CONTINUE_CALLBACK)
    builder.button(text="Stories", callback_data=STORIES_CALLBACK)
    builder.adjust(1)
    return builder.as_markup()
