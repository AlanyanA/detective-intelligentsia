from pathlib import Path

import pytest

from detective_bot.db import Database


@pytest.mark.asyncio
async def test_database_initializes(tmp_path: Path) -> None:
    database_path = tmp_path / "game.db"
    await Database(database_path).initialize()
    assert database_path.exists()
