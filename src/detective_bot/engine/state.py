from __future__ import annotations

from detective_bot.models.player_state import PlayerState
from detective_bot.models.story import StateChanges


class StateMutator:
    def apply(self, state: PlayerState, changes: StateChanges) -> PlayerState:
        state.flags.update(changes.set_flags)
        state.inventory.update(changes.add_inventory)
        state.inventory.difference_update(changes.remove_inventory)
        state.discovered_clues.update(changes.discover_clues)
        for suspect, delta in changes.suspect_scores.items():
            state.suspect_scores[suspect] = state.suspect_scores.get(suspect, 0) + delta
        state.mark_updated()
        return state

    def move_to_scene(self, state: PlayerState, scene_id: str) -> PlayerState:
        state.current_scene = scene_id
        state.visited_scenes.add(scene_id)
        state.mark_updated()
        return state
