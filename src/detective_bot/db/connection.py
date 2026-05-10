from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


class Database:
    def __init__(self, sqlite_path: Path) -> None:
        self._path = sqlite_path

    async def connect(self) -> aiosqlite.Connection:
        if self._path.parent != Path("."):
            self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = await aiosqlite.connect(self._path)
        connection.row_factory = aiosqlite.Row
        await connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @asynccontextmanager
    async def session(self) -> AsyncIterator[aiosqlite.Connection]:
        connection = await self.connect()
        try:
            yield connection
        finally:
            await connection.close()

    async def initialize(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        async with self.session() as connection:
            await connection.executescript(schema_path.read_text(encoding="utf-8"))
            await connection.commit()
