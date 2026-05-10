from __future__ import annotations

from dataclasses import dataclass

from detective_bot.db.connection import Database
from detective_bot.db.repositories import AnalyticsRepository, PlayerStateRepository
from detective_bot.engine.exceptions import InvalidChoiceError
from detective_bot.engine.renderer import SceneRenderer
from detective_bot.engine.story_loader import StoryLoader
from detective_bot.models.analytics import AnalyticsEvent
from detective_bot.models.player_state import PlayerState
from detective_bot.models.rendered import RenderedScene


@dataclass(frozen=True)
class GameView:
    rendered: RenderedScene
    state: PlayerState


class GameService:
    def __init__(self, database: Database, loader: StoryLoader, renderer: SceneRenderer) -> None:
        self._database = database
        self._loader = loader
        self._renderer = renderer

    async def start_story(self, user_id: int, story_id: str, restart: bool = False) -> GameView:
        story = self._loader.load(story_id)
        async with self._database.session() as connection:
            states = PlayerStateRepository(connection)
            analytics = AnalyticsRepository(connection)
            if restart:
                await states.delete(user_id, story_id)
                await analytics.log(AnalyticsEvent("story_restarted", user_id, story_id))
            state, rendered = self._renderer.start_story(story, user_id)
            await states.save(state)
            await analytics.log(AnalyticsEvent("story_started", user_id, story_id, rendered.scene_id))
            await self._log_scene_and_ending(analytics, user_id, state, rendered)
        return GameView(rendered=rendered, state=state)

    async def continue_latest(self, user_id: int) -> GameView | None:
        async with self._database.session() as connection:
            states = PlayerStateRepository(connection)
            state = await states.get_latest_for_user(user_id)
            if state is None:
                return None
            story = self._loader.load(state.story_id)
            rendered = self._renderer.render_current(story, state)
            analytics = AnalyticsRepository(connection)
            await analytics.log(AnalyticsEvent("story_continued", user_id, state.story_id, rendered.scene_id))
            await self._log_scene_and_ending(analytics, user_id, state, rendered)
            return GameView(rendered=rendered, state=state)

    async def continue_story(self, user_id: int, story_id: str) -> GameView | None:
        story = self._loader.load(story_id)
        async with self._database.session() as connection:
            states = PlayerStateRepository(connection)
            state = await states.get(user_id, story_id)
            if state is None:
                return None
            rendered = self._renderer.render_current(story, state)
            analytics = AnalyticsRepository(connection)
            await analytics.log(AnalyticsEvent("story_continued", user_id, story_id, rendered.scene_id))
            await self._log_scene_and_ending(analytics, user_id, state, rendered)
            return GameView(rendered=rendered, state=state)

    async def choose(self, user_id: int, story_id: str, choice_id: str) -> GameView:
        story = self._loader.load(story_id)
        async with self._database.session() as connection:
            states = PlayerStateRepository(connection)
            state = await states.get(user_id, story_id)
            if state is None:
                state, _ = self._renderer.start_story(story, user_id)
            previous_scene_id = state.current_scene
            state, rendered, choice = self._renderer.choose(story, state, choice_id)
            await states.save(state)
            analytics = AnalyticsRepository(connection)
            await analytics.log(
                AnalyticsEvent(
                    event_type="choice_selected",
                    user_id=user_id,
                    story_id=story_id,
                    scene_id=previous_scene_id,
                    choice_id=choice.id,
                )
            )
            await self._log_scene_and_ending(analytics, user_id, state, rendered)
        return GameView(rendered=rendered, state=state)

    async def choose_latest(self, user_id: int, choice_id: str) -> GameView:
        async with self._database.session() as connection:
            states = PlayerStateRepository(connection)
            state = await states.get_latest_for_user(user_id)
            if state is None:
                raise InvalidChoiceError("No active story for choice callback.")
            story = self._loader.load(state.story_id)
            previous_scene_id = state.current_scene
            state, rendered, choice = self._renderer.choose(story, state, choice_id)
            await states.save(state)
            analytics = AnalyticsRepository(connection)
            await analytics.log(
                AnalyticsEvent(
                    event_type="choice_selected",
                    user_id=user_id,
                    story_id=state.story_id,
                    scene_id=previous_scene_id,
                    choice_id=choice.id,
                )
            )
            await self._log_scene_and_ending(analytics, user_id, state, rendered)
            return GameView(rendered=rendered, state=state)

    async def restart_latest(self, user_id: int) -> GameView | None:
        async with self._database.session() as connection:
            state = await PlayerStateRepository(connection).get_latest_for_user(user_id)
        if state is None:
            return None
        return await self.start_story(user_id, state.story_id, restart=True)

    async def list_user_states(self, user_id: int) -> list[PlayerState]:
        async with self._database.session() as connection:
            return await PlayerStateRepository(connection).list_for_user(user_id)

    async def _log_scene_and_ending(
        self,
        analytics: AnalyticsRepository,
        user_id: int,
        state: PlayerState,
        rendered: RenderedScene,
    ) -> None:
        await analytics.log(
            AnalyticsEvent(
                event_type="scene_visit",
                user_id=user_id,
                story_id=rendered.story_id,
                scene_id=rendered.scene_id,
            )
        )
        if rendered.is_ending:
            await analytics.log(
                AnalyticsEvent(
                    event_type="ending_reached",
                    user_id=user_id,
                    story_id=rendered.story_id,
                    scene_id=rendered.scene_id,
                    ending_id=rendered.ending_id,
                )
            )
