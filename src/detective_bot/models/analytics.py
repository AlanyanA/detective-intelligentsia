from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AnalyticsEvent:
    event_type: str
    user_id: int
    story_id: str
    scene_id: str | None = None
    choice_id: str | None = None
    ending_id: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime | None = None
