from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator


JsonValue = str | int | float | bool | None | dict[str, Any] | list[Any]


class InventoryOperation(StrEnum):
    ADD = "add"
    REMOVE = "remove"


class AssetKind(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class MediaAsset(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: AssetKind
    path: str
    caption: str | None = None


class EndingMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    outcome: Literal["success", "partial", "failure", "secret"] = "partial"
    completion: bool = True


class Condition(BaseModel):
    """Recursive story condition tree.

    Supported examples:
    {"flag": "searched_body", "equals": true}
    {"inventory": "rusty_key"}
    {"visited": "crime_scene"}
    {"and": [{"flag": "x"}, {"not": {"inventory": "y"}}]}
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    all_: tuple[Condition, ...] | None = Field(default=None, alias="and")
    any_: tuple[Condition, ...] | None = Field(default=None, alias="or")
    not_: Condition | None = Field(default=None, alias="not")
    flag: str | None = None
    equals: JsonValue | None = None
    exists: bool | None = None
    inventory: str | None = None
    clue: str | None = None
    visited: str | None = None
    suspect_score: str | None = None
    gte: int | None = None
    lte: int | None = None

    @model_validator(mode="after")
    def validate_operator(self) -> Condition:
        operators = [
            self.all_ is not None,
            self.any_ is not None,
            self.not_ is not None,
            self.flag is not None,
            self.inventory is not None,
            self.clue is not None,
            self.visited is not None,
            self.suspect_score is not None,
        ]
        if sum(operators) != 1:
            raise ValueError("Condition must contain exactly one root operator/check.")
        if self.suspect_score and self.gte is None and self.lte is None:
            raise ValueError("suspect_score conditions require gte and/or lte.")
        return self


class StateChanges(BaseModel):
    model_config = ConfigDict(frozen=True)

    set_flags: Mapping[str, JsonValue] = Field(default_factory=dict)
    add_inventory: tuple[str, ...] = Field(default_factory=tuple)
    remove_inventory: tuple[str, ...] = Field(default_factory=tuple)
    discover_clues: tuple[str, ...] = Field(default_factory=tuple)
    suspect_scores: Mapping[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_mappings(self) -> StateChanges:
        object.__setattr__(self, "set_flags", MappingProxyType(dict(self.set_flags)))
        object.__setattr__(self, "suspect_scores", MappingProxyType(dict(self.suspect_scores)))
        return self


class Choice(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    next_scene: str
    conditions: tuple[Condition, ...] = Field(default_factory=tuple)
    effects: StateChanges = Field(default_factory=StateChanges)


class Scene(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    choices: tuple[Choice, ...] = Field(default_factory=tuple)
    conditions: tuple[Condition, ...] = Field(default_factory=tuple)
    effects: StateChanges = Field(default_factory=StateChanges)
    media: tuple[MediaAsset, ...] = Field(default_factory=tuple)
    ending: EndingMetadata | None = None

    @model_validator(mode="after")
    def validate_telegram_choice_count(self) -> Scene:
        if len(self.choices) > 4:
            raise ValueError("Telegram UX supports a maximum of 4 choices per scene.")
        return self


class StoryManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    version: str = "1.0.0"
    author: str | None = None
    start_scene: str
    description: str = ""
    language: str = "en"


class Story(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    manifest: StoryManifest
    scenes: Mapping[str, Scene]
    root_path: Path

    @model_validator(mode="after")
    def freeze_scenes(self) -> Story:
        object.__setattr__(self, "scenes", MappingProxyType(dict(self.scenes)))
        return self

    def get_scene(self, scene_id: str) -> Scene:
        try:
            return self.scenes[scene_id]
        except KeyError as exc:
            raise KeyError(f"Scene '{scene_id}' does not exist in story '{self.manifest.id}'.") from exc
