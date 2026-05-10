from pathlib import Path

from detective_bot.engine.story_loader import StoryLoader
from detective_bot.services.story_catalog import StoryCatalog


def test_catalog_uses_manifests_without_validating_all_scenes() -> None:
    catalog = StoryCatalog(StoryLoader(Path("stories")))

    story_ids = {story.id for story in catalog.list_stories()}

    assert "case_003_football" in story_ids
