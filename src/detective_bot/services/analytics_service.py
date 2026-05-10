from __future__ import annotations

from detective_bot.db.repositories import AnalyticsRepository
from detective_bot.models.analytics import AnalyticsEvent
from detective_bot.models.rendered import RenderedScene


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self._repository = repository

    async def log_scene_visit(self, user_id: int, rendered: RenderedScene) -> None:
        await self._repository.log(
            AnalyticsEvent(
                event_type="scene_visit",
                user_id=user_id,
                story_id=rendered.story_id,
                scene_id=rendered.scene_id,
            )
        )

    async def log_choice(self, user_id: int, rendered: RenderedScene, choice_id: str) -> None:
        await self._repository.log(
            AnalyticsEvent(
                event_type="choice_selected",
                user_id=user_id,
                story_id=rendered.story_id,
                scene_id=rendered.scene_id,
                choice_id=choice_id,
            )
        )

    async def log_ending(self, user_id: int, rendered: RenderedScene, ending_id: str | None) -> None:
        await self._repository.log(
            AnalyticsEvent(
                event_type="ending_reached",
                user_id=user_id,
                story_id=rendered.story_id,
                scene_id=rendered.scene_id,
                ending_id=ending_id,
            )
        )
