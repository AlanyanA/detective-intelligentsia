from __future__ import annotations

from detective_bot.models.player_state import PlayerState
from detective_bot.models.story import Condition


class ConditionEvaluator:
    def evaluate_all(self, conditions: tuple[Condition, ...], state: PlayerState) -> bool:
        return all(self.evaluate(condition, state) for condition in conditions)

    def evaluate(self, condition: Condition, state: PlayerState) -> bool:
        if condition.all_ is not None:
            return all(self.evaluate(child, state) for child in condition.all_)
        if condition.any_ is not None:
            return any(self.evaluate(child, state) for child in condition.any_)
        if condition.not_ is not None:
            return not self.evaluate(condition.not_, state)
        if condition.flag is not None:
            return self._evaluate_flag(condition, state)
        if condition.inventory is not None:
            return condition.inventory in state.inventory
        if condition.clue is not None:
            return condition.clue in state.discovered_clues
        if condition.visited is not None:
            return condition.visited in state.visited_scenes
        if condition.suspect_score is not None:
            return self._evaluate_suspect_score(condition, state)
        return False

    def _evaluate_flag(self, condition: Condition, state: PlayerState) -> bool:
        value = state.flags.get(condition.flag)
        if condition.exists is not None:
            return (condition.flag in state.flags) is condition.exists
        if condition.equals is not None:
            return value == condition.equals
        return bool(value)

    def _evaluate_suspect_score(self, condition: Condition, state: PlayerState) -> bool:
        score = state.suspect_scores.get(condition.suspect_score or "", 0)
        if condition.gte is not None and score < condition.gte:
            return False
        if condition.lte is not None and score > condition.lte:
            return False
        return True
