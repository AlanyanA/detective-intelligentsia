from pathlib import Path

import pytest

from detective_bot.telegram.rendering import TelegramSceneSender


def test_media_sender_blocks_path_escape() -> None:
    sender = TelegramSceneSender(Path("stories"))

    with pytest.raises(ValueError):
        sender._resolve_story_asset("case_001", "../../.env")
