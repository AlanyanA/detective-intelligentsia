from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import aiosqlite

from detective_bot.models.analytics import AnalyticsEvent
from detective_bot.models.player_state import PlayerState


class PlayerStateRepository:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    async def get(self, user_id: int, story_id: str) -> PlayerState | None:
        cursor = await self._connection.execute(
            """
            SELECT * FROM player_states
            WHERE user_id = ? AND story_id = ?
            """,
            (user_id, story_id),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return self._row_to_state(row) if row else None

    async def get_latest_for_user(self, user_id: int) -> PlayerState | None:
        cursor = await self._connection.execute(
            """
            SELECT * FROM player_states
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return self._row_to_state(row) if row else None

    async def list_for_user(self, user_id: int) -> list[PlayerState]:
        cursor = await self._connection.execute(
            """
            SELECT * FROM player_states
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [self._row_to_state(row) for row in rows]

    async def save(self, state: PlayerState) -> None:
        state.mark_updated()
        await self._connection.execute(
            """
            INSERT INTO player_states (
                user_id, story_id, current_scene, visited_scenes, flags, inventory,
                discovered_clues, suspect_scores, endings_reached, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, story_id) DO UPDATE SET
                current_scene = excluded.current_scene,
                visited_scenes = excluded.visited_scenes,
                flags = excluded.flags,
                inventory = excluded.inventory,
                discovered_clues = excluded.discovered_clues,
                suspect_scores = excluded.suspect_scores,
                endings_reached = excluded.endings_reached,
                updated_at = excluded.updated_at
            """,
            (
                state.user_id,
                state.story_id,
                state.current_scene,
                json.dumps(sorted(state.visited_scenes)),
                json.dumps(state.flags),
                json.dumps(sorted(state.inventory)),
                json.dumps(sorted(state.discovered_clues)),
                json.dumps(state.suspect_scores),
                json.dumps(sorted(state.endings_reached)),
                state.created_at.isoformat(),
                state.updated_at.isoformat(),
            ),
        )
        await self._connection.commit()

    async def delete(self, user_id: int, story_id: str) -> None:
        await self._connection.execute(
            "DELETE FROM player_states WHERE user_id = ? AND story_id = ?",
            (user_id, story_id),
        )
        await self._connection.commit()

    def _row_to_state(self, row: aiosqlite.Row) -> PlayerState:
        return PlayerState(
            user_id=row["user_id"],
            story_id=row["story_id"],
            current_scene=row["current_scene"],
            visited_scenes=set(json.loads(row["visited_scenes"])),
            flags=json.loads(row["flags"]),
            inventory=set(json.loads(row["inventory"])),
            discovered_clues=set(json.loads(row["discovered_clues"])),
            suspect_scores=json.loads(row["suspect_scores"]),
            endings_reached=set(json.loads(row["endings_reached"])),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class AnalyticsRepository:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    async def log(self, event: AnalyticsEvent) -> None:
        created_at = event.created_at or datetime.now(UTC)
        await self._connection.execute(
            """
            INSERT INTO analytics_events (
                event_type, user_id, story_id, scene_id, choice_id, ending_id, payload, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_type,
                event.user_id,
                event.story_id,
                event.scene_id,
                event.choice_id,
                event.ending_id,
                json.dumps(event.payload or {}),
                created_at.isoformat(),
            ),
        )
        await self._connection.commit()

    async def count_by_choice(self, story_id: str) -> list[dict[str, Any]]:
        cursor = await self._connection.execute(
            """
            SELECT scene_id, choice_id, COUNT(*) AS count
            FROM analytics_events
            WHERE story_id = ? AND event_type = 'choice_selected'
            GROUP BY scene_id, choice_id
            ORDER BY count DESC
            """,
            (story_id,),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]
