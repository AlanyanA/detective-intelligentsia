from __future__ import annotations

from detective_bot.engine.conditions import ConditionEvaluator
from detective_bot.engine.exceptions import InvalidChoiceError, SceneAccessDeniedError
from detective_bot.engine.state import StateMutator
from detective_bot.models.player_state import PlayerState
from detective_bot.models.rendered import RenderedChoice, RenderedScene
from detective_bot.models.story import Choice, Scene, Story


class SceneRenderer:
    def __init__(self, condition_evaluator: ConditionEvaluator, state_mutator: StateMutator) -> None:
        self._conditions = condition_evaluator
        self._state_mutator = state_mutator

    def render_current(self, story: Story, state: PlayerState) -> RenderedScene:
        scene = story.get_scene(state.current_scene)
        return self._render(story, state, scene)

    def start_story(self, story: Story, user_id: int) -> tuple[PlayerState, RenderedScene]:
        state = PlayerState(
            user_id=user_id,
            story_id=story.manifest.id,
            current_scene=story.manifest.start_scene,
            visited_scenes={story.manifest.start_scene},
        )
        scene = story.get_scene(story.manifest.start_scene)
        self._state_mutator.apply(state, scene.effects)
        if scene.ending:
            state.endings_reached.add(scene.ending.id)
        return state, self._render(story, state, scene)

    def choose(self, story: Story, state: PlayerState, choice_id: str) -> tuple[PlayerState, RenderedScene, Choice]:
        current = story.get_scene(state.current_scene)
        choice = self._find_available_choice(current, state, choice_id)
        self._state_mutator.apply(state, choice.effects)
        next_scene = story.get_scene(choice.next_scene)
        if not self._conditions.evaluate_all(next_scene.conditions, state):
            raise SceneAccessDeniedError(
                f"Scene '{next_scene.id}' conditions are not satisfied after choice '{choice.id}'."
            )
        self._state_mutator.move_to_scene(state, next_scene.id)
        self._state_mutator.apply(state, next_scene.effects)
        if next_scene.ending:
            state.endings_reached.add(next_scene.ending.id)
            state.mark_updated()
        return state, self._render(story, state, next_scene), choice

    def _render(self, story: Story, state: PlayerState, scene: Scene) -> RenderedScene:
        if not self._conditions.evaluate_all(scene.conditions, state):
            raise SceneAccessDeniedError(f"Scene '{scene.id}' conditions are not satisfied.")
        visible_choices = tuple(
            RenderedChoice(id=choice.id, text=choice.text)
            for choice in scene.choices
            if self._conditions.evaluate_all(choice.conditions, state)
        )
        return RenderedScene(
            story_id=story.manifest.id,
            scene_id=scene.id,
            text=scene.text,
            choices=visible_choices,
            media=scene.media,
            is_ending=scene.ending is not None,
            ending_id=scene.ending.id if scene.ending else None,
        )

    def _find_available_choice(self, scene: Scene, state: PlayerState, choice_id: str) -> Choice:
        for choice in scene.choices:
            if choice.id == choice_id and self._conditions.evaluate_all(choice.conditions, state):
                return choice
        raise InvalidChoiceError(f"Choice '{choice_id}' is not available in scene '{scene.id}'.")
