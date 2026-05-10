from __future__ import annotations

from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, Message

from detective_bot.models.rendered import RenderedScene
from detective_bot.models.story import AssetKind, MediaAsset
from detective_bot.telegram.keyboards import scene_choices_keyboard


class TelegramSceneSender:
    def __init__(self, stories_path: Path) -> None:
        self._stories_path = stories_path

    async def send_scene(self, bot: Bot, chat_id: int, rendered: RenderedScene) -> None:
        for media in rendered.media:
            await self._send_media(bot, chat_id, rendered.story_id, media)

        await bot.send_message(
            chat_id=chat_id,
            text=rendered.text,
            reply_markup=scene_choices_keyboard(rendered.choices, rendered.is_ending),
        )

    async def answer_scene(self, message: Message, rendered: RenderedScene) -> None:
        await self.send_scene(message.bot, message.chat.id, rendered)

    async def _send_media(self, bot: Bot, chat_id: int, story_id: str, media: MediaAsset) -> None:
        path = self._resolve_story_asset(story_id, media.path)
        file = FSInputFile(path)
        if media.kind == AssetKind.IMAGE:
            await bot.send_photo(chat_id=chat_id, photo=file, caption=media.caption)
        elif media.kind == AssetKind.AUDIO:
            await bot.send_audio(chat_id=chat_id, audio=file, caption=media.caption)
        elif media.kind == AssetKind.DOCUMENT:
            await bot.send_document(chat_id=chat_id, document=file, caption=media.caption)

    def _resolve_story_asset(self, story_id: str, media_path: str) -> Path:
        story_root = (self._stories_path / story_id).resolve()
        asset_path = (story_root / media_path).resolve()
        if not self._is_relative_to(asset_path, story_root):
            raise ValueError(f"Media path escapes story folder: {media_path}")
        return asset_path

    def _is_relative_to(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
