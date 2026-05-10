from dataclasses import dataclass

from detective_bot.models.story import MediaAsset


@dataclass(frozen=True)
class RenderedChoice:
    id: str
    text: str


@dataclass(frozen=True)
class RenderedScene:
    story_id: str
    scene_id: str
    text: str
    choices: tuple[RenderedChoice, ...]
    media: tuple[MediaAsset, ...]
    is_ending: bool
    ending_id: str | None = None
