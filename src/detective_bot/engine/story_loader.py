from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from detective_bot.engine.exceptions import StoryNotFoundError
from detective_bot.models.story import Scene, Story, StoryManifest


class StoryLoader:
    def __init__(self, stories_path: Path) -> None:
        self._stories_path = stories_path

    def list_story_ids(self) -> list[str]:
        if not self._stories_path.exists():
            return []
        return sorted(
            path.name for path in self._stories_path.iterdir() if path.is_dir() and not path.name.startswith(".")
        )

    def load(self, story_id: str) -> Story:
        root = self._stories_path / story_id
        if not root.exists():
            raise StoryNotFoundError(f"Story '{story_id}' was not found in {self._stories_path}.")

        manifest = StoryManifest.model_validate(self._read_data(root / "story.yaml", root / "story.json"))
        scenes_dir = root / "scenes"
        scenes: dict[str, Scene] = {}
        for scene_file in sorted([*scenes_dir.glob("*.yaml"), *scenes_dir.glob("*.yml"), *scenes_dir.glob("*.json")]):
            scene = Scene.model_validate(self._read_data(scene_file))
            if scene.id in scenes:
                raise ValueError(f"Duplicate scene id '{scene.id}' in {scene_file}.")
            scenes[scene.id] = scene

        return Story(manifest=manifest, scenes=scenes, root_path=root)

    def _read_data(self, *candidates: Path) -> dict[str, Any]:
        for path in candidates:
            if path.exists():
                with path.open("r", encoding="utf-8") as file:
                    if path.suffix in {".yaml", ".yml"}:
                        data = yaml.safe_load(file)
                    else:
                        data = json.load(file)
                if not isinstance(data, dict):
                    raise ValueError(f"{path} must contain a mapping/object.")
                return data
        joined = ", ".join(str(path) for path in candidates)
        raise FileNotFoundError(f"None of these story files exist: {joined}")
