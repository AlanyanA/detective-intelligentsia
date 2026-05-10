from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class PlayerState(BaseModel):
    user_id: int
    story_id: str
    current_scene: str
    visited_scenes: set[str] = Field(default_factory=set)
    flags: dict[str, Any] = Field(default_factory=dict)
    inventory: set[str] = Field(default_factory=set)
    discovered_clues: set[str] = Field(default_factory=set)
    suspect_scores: dict[str, int] = Field(default_factory=dict)
    endings_reached: set[str] = Field(default_factory=set)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def mark_updated(self) -> None:
        self.updated_at = datetime.now(UTC)
