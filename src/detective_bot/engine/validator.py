from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

from detective_bot.models.story import Condition, Story

MAX_CALLBACK_DATA_BYTES = 64


@dataclass
class ValidationReport:
    story_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class StoryValidator:
    def validate(self, story: Story) -> ValidationReport:
        report = ValidationReport(story_id=story.manifest.id)
        self._validate_start_scene(story, report)
        self._validate_references(story, report)
        self._validate_reachability(story, report)
        self._validate_dead_ends(story, report)
        self._validate_cycles(story, report)
        self._validate_conditions(story, report)
        self._validate_callback_lengths(story, report)
        self._validate_assets(story, report)
        return report

    def _validate_start_scene(self, story: Story, report: ValidationReport) -> None:
        if story.manifest.start_scene not in story.scenes:
            report.errors.append(f"start_scene '{story.manifest.start_scene}' does not exist.")

    def _validate_references(self, story: Story, report: ValidationReport) -> None:
        for scene in story.scenes.values():
            for choice in scene.choices:
                if choice.next_scene not in story.scenes:
                    report.errors.append(
                        f"Scene '{scene.id}' choice '{choice.id}' references missing scene '{choice.next_scene}'."
                    )

    def _validate_reachability(self, story: Story, report: ValidationReport) -> None:
        if story.manifest.start_scene not in story.scenes:
            return
        reachable = self._reachable_scene_ids(story)
        for scene_id in sorted(set(story.scenes) - reachable):
            report.warnings.append(f"Scene '{scene_id}' is unreachable from start_scene.")

    def _validate_dead_ends(self, story: Story, report: ValidationReport) -> None:
        for scene in story.scenes.values():
            if not scene.choices and scene.ending is None:
                report.errors.append(f"Scene '{scene.id}' has no choices and no ending metadata.")

    def _validate_cycles(self, story: Story, report: ValidationReport) -> None:
        graph = self._graph(story)
        visited: set[str] = set()
        active: set[str] = set()
        cycles: set[tuple[str, ...]] = set()

        def dfs(scene_id: str, path: list[str]) -> None:
            visited.add(scene_id)
            active.add(scene_id)
            for next_id in graph[scene_id]:
                if next_id not in story.scenes:
                    continue
                if next_id not in visited:
                    dfs(next_id, [*path, next_id])
                elif next_id in active:
                    cycle_start = path.index(next_id) if next_id in path else 0
                    cycles.add(tuple(path[cycle_start:] + [next_id]))
            active.remove(scene_id)

        if story.manifest.start_scene in story.scenes:
            dfs(story.manifest.start_scene, [story.manifest.start_scene])
        for cycle in sorted(cycles):
            report.warnings.append(f"Cycle detected: {' -> '.join(cycle)}")

    def _validate_conditions(self, story: Story, report: ValidationReport) -> None:
        for scene in story.scenes.values():
            for condition in scene.conditions:
                self._validate_condition(condition, story, report, f"scene '{scene.id}'")
            for choice in scene.choices:
                for condition in choice.conditions:
                    self._validate_condition(condition, story, report, f"choice '{scene.id}.{choice.id}'")

    def _validate_condition(
        self,
        condition: Condition,
        story: Story,
        report: ValidationReport,
        location: str,
    ) -> None:
        if condition.visited is not None and condition.visited not in story.scenes:
            report.errors.append(f"{location} condition references unknown visited scene '{condition.visited}'.")
        for child in [*(condition.all_ or []), *(condition.any_ or [])]:
            self._validate_condition(child, story, report, location)
        if condition.not_ is not None:
            self._validate_condition(condition.not_, story, report, location)

    def _validate_assets(self, story: Story, report: ValidationReport) -> None:
        for scene in story.scenes.values():
            for media in scene.media:
                asset_path = (story.root_path / media.path).resolve()
                root = story.root_path.resolve()
                if not self._is_relative_to(asset_path, root):
                    report.errors.append(f"Scene '{scene.id}' asset escapes story folder: {media.path}")
                elif not asset_path.exists():
                    report.errors.append(f"Scene '{scene.id}' references missing asset: {media.path}")

    def _validate_callback_lengths(self, story: Story, report: ValidationReport) -> None:
        story_callback = f"s:{story.manifest.id}"
        if len(story_callback.encode("utf-8")) > MAX_CALLBACK_DATA_BYTES:
            report.errors.append(
                f"Story id '{story.manifest.id}' makes callback_data exceed {MAX_CALLBACK_DATA_BYTES} bytes."
            )
        for scene in story.scenes.values():
            for choice in scene.choices:
                choice_callback = f"c:{choice.id}"
                if len(choice_callback.encode("utf-8")) > MAX_CALLBACK_DATA_BYTES:
                    report.errors.append(
                        f"Choice '{scene.id}.{choice.id}' makes callback_data exceed "
                        f"{MAX_CALLBACK_DATA_BYTES} bytes."
                    )

    def _reachable_scene_ids(self, story: Story) -> set[str]:
        graph = self._graph(story)
        reachable: set[str] = set()
        queue: deque[str] = deque([story.manifest.start_scene])
        while queue:
            scene_id = queue.popleft()
            if scene_id in reachable or scene_id not in story.scenes:
                continue
            reachable.add(scene_id)
            queue.extend(graph[scene_id])
        return reachable

    def _graph(self, story: Story) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = defaultdict(list)
        for scene_id, scene in story.scenes.items():
            graph[scene_id].extend(choice.next_scene for choice in scene.choices)
        return graph

    def _is_relative_to(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
