from pathlib import Path

import pytest

from detective_bot.engine import ConditionEvaluator, SceneRenderer, StateMutator, StoryLoader, StoryValidator
from detective_bot.engine.exceptions import InvalidChoiceError
from detective_bot.telegram.callbacks import choice_callback


def test_example_story_validates() -> None:
    loader = StoryLoader(Path("stories"))
    validator = StoryValidator()
    for story_id in ("case_001", "case_002"):
        report = validator.validate(loader.load(story_id))
        assert report.errors == []


def test_hidden_safe_choice_requires_inventory() -> None:
    story = StoryLoader(Path("stories")).load("case_001")
    renderer = SceneRenderer(ConditionEvaluator(), StateMutator())
    state, _ = renderer.start_story(story, user_id=1)

    state, rendered, _ = renderer.choose(story, state, "enter_study")
    choice_ids = {choice.id for choice in rendered.choices}
    assert "open_safe" not in choice_ids

    state, _, _ = renderer.choose(story, state, "inspect_body")
    state, _, _ = renderer.choose(story, state, "take_key")
    state, rendered, _ = renderer.choose(story, state, "return")
    choice_ids = {choice.id for choice in rendered.choices}
    assert "open_safe" in choice_ids


def test_nested_and_or_conditions_work_for_case_002() -> None:
    story = StoryLoader(Path("stories")).load("case_002")
    renderer = SceneRenderer(ConditionEvaluator(), StateMutator())
    state, rendered = renderer.start_story(story, user_id=1)
    assert rendered.scene_id == "station"
    assert "open_service_hatch" not in {choice.id for choice in rendered.choices}

    state, _, _ = renderer.choose(story, state, "search_console")
    state, _, _ = renderer.choose(story, state, "copy_logs")
    state, rendered, _ = renderer.choose(story, state, "back")
    assert "open_service_hatch" not in {choice.id for choice in rendered.choices}

    state, _, _ = renderer.choose(story, state, "inspect_tracks")
    state, _, _ = renderer.choose(story, state, "pocket_badge")
    state, rendered, _ = renderer.choose(story, state, "back")
    assert "open_service_hatch" in {choice.id for choice in rendered.choices}

    state, _, _ = renderer.choose(story, state, "open_service_hatch")
    state, _, _ = renderer.choose(story, state, "crawl_to_mast")
    state, rendered, _ = renderer.choose(story, state, "secret_deduction")
    assert rendered.is_ending is True
    assert rendered.ending_id == "perfect_signal"


def test_story_objects_are_immutable() -> None:
    story = StoryLoader(Path("stories")).load("case_001")

    with pytest.raises(TypeError):
        story.scenes["new_scene"] = story.get_scene("intro")

    with pytest.raises(Exception):
        story.get_scene("intro").choices += ()


def test_choice_callback_payload_is_compact() -> None:
    data = choice_callback("secret_deduction")
    assert data == "c:secret_deduction"
    assert len(data.encode("utf-8")) <= 64


def test_two_different_stories_run_without_code_changes() -> None:
    loader = StoryLoader(Path("stories"))
    renderer = SceneRenderer(ConditionEvaluator(), StateMutator())

    case_001 = loader.load("case_001")
    case_002 = loader.load("case_002")

    state_001, rendered_001 = renderer.start_story(case_001, user_id=1)
    state_002, rendered_002 = renderer.start_story(case_002, user_id=1)

    assert rendered_001.scene_id == "intro"
    assert rendered_002.scene_id == "station"
    assert state_001.story_id == "case_001"
    assert state_002.story_id == "case_002"

    with pytest.raises(InvalidChoiceError):
        renderer.choose(case_001, state_001, "search_console")
