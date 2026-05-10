from pathlib import Path

import pytest

from detective_bot.db import Database
from detective_bot.engine import ConditionEvaluator, SceneRenderer, StateMutator, StoryLoader
from detective_bot.services import GameService


@pytest.mark.asyncio
async def test_restart_resets_current_run_state(tmp_path: Path) -> None:
    database = Database(tmp_path / "game.db")
    await database.initialize()
    service = GameService(
        database,
        StoryLoader(Path("stories")),
        SceneRenderer(ConditionEvaluator(), StateMutator()),
    )

    await service.start_story(42, "case_001")
    await service.choose(42, "case_001", "enter_study")
    await service.choose(42, "case_001", "inspect_body")
    progressed = await service.choose(42, "case_001", "take_key")
    assert "brass_key" in progressed.state.inventory
    assert "body" in progressed.state.visited_scenes

    restarted = await service.start_story(42, "case_001", restart=True)
    assert restarted.state.current_scene == "intro"
    assert restarted.state.visited_scenes == {"intro"}
    assert restarted.state.flags == {}
    assert restarted.state.inventory == set()
    assert restarted.state.discovered_clues == set()
    assert restarted.state.suspect_scores == {}
    assert restarted.state.endings_reached == set()
