from __future__ import annotations

from dataclasses import dataclass

from detective_bot.engine.story_loader import StoryLoader


@dataclass(frozen=True)
class StorySummary:
    id: str
    title: str
    description: str
    language: str


class StoryCatalog:
    def __init__(self, loader: StoryLoader) -> None:
        self._loader = loader

    def list_stories(self) -> list[StorySummary]:
        summaries: list[StorySummary] = []
        for story_id in self._loader.list_story_ids():
            story = self._loader.load(story_id)
            summaries.append(
                StorySummary(
                    id=story.manifest.id,
                    title=story.manifest.title,
                    description=story.manifest.description,
                    language=story.manifest.language,
                )
            )
        return summaries
