from __future__ import annotations
import arcade
from typing import TYPE_CHECKING
from assets.param_map import MOVEMENT_SPEED
from character.character_classes import PNJState, Weapon
from map.ui_menus import StatsView

if TYPE_CHECKING:
    from map.map_base import BaseGameView


_MOVE_KEYS = {
    arcade.key.D: ("x",  1, "right"),
    arcade.key.Q: ("x", -1, "left"),
    arcade.key.Z: ("y",  1, "up"),
    arcade.key.S: ("y", -1, "down"),
}


class InputHandler:
    def __init__(self, game_view: BaseGameView):
        self.game_view   = game_view
        self._keys_held: set = set()

    def on_mouse_press(self, x: float, y: float, button, modifiers) -> None:
        gv = self.game_view
        qx, qy = gv.quest_x, gv.quest_y
        qw, qh = gv.quest_width / 2, gv.quest_height / 2
        if qx - qw <= x <= qx + qw and qy - qh <= y <= qy + qh:
            gv.show_side_bar = not gv.show_side_bar

    def handle_key_press(self, key, modifiers) -> None:
        gv = self.game_view
        if gv.auto_walk_active:
            return
        if gv.kyle_cutscene.active:
            if key == arcade.key.ENTER:
                done = gv.kyle_cutscene.advance()
                if done:
                    gv.quest_manager.complete_talk_objective("Kyle")
                    if gv.player_sprite is not None:
                        gv.player_sprite.weapon = Weapon("Pistolet", damage_min=1.0, damage_max=1.5,
                                                              bullet_color=(255, 120, 0))
                    gv.start_auto_walk(755.0, 745.0)
                    if hasattr(gv, '_start_kyle_walk'):
                        gv._on_auto_walk_done = lambda: gv._start_kyle_walk(772.0, 236.0)
            return
        if gv.sylvain_cutscene.active:
            if key == arcade.key.ENTER:
                done = gv.sylvain_cutscene.advance()
                if done:
                    gv.quest_manager.complete_talk_objective("Sylvain")
            return
        if gv.jc_cutscene.active:
            if key == arcade.key.ENTER:
                done = gv.jc_cutscene.advance()
                if done:
                    gv.quest_manager.complete_talk_objective("Jean christophe")
            return
        if gv.guy_cutscene.active:
            if key == arcade.key.ENTER:
                done = gv.guy_cutscene.advance()
                if done:
                    gv.quest_manager.complete_talk_objective("Guy")
            return
        if key == arcade.key.ESCAPE:
            if gv.is_typing:
                gv.is_typing = False
                gv.last_response = ""
                gv.current_input = ""
                if gv.current_pnj is not None:
                    gv.current_pnj.leave_dialogue()
                gv.current_pnj = None
                return
            if gv.show_menu:
                if gv.menu.has_sub():
                    gv.menu.handle_key(key)
                else:
                    gv.show_menu = False
                    gv.menu.reset()
            else:
                gv.show_menu = True
                gv.menu.reset()
            return
        if gv.show_menu:
            gv.menu.handle_key(key)
            return
        self._to_reinit(key)
        if self._handle_movement_keys(key):
            return
        self._to_show_stat(key)
        if self._to_dialogue(key):
            return
        self._up_stat(key)

    def _handle_movement_keys(self, key) -> bool:
        if self.game_view.is_typing:
            return False
        if key not in _MOVE_KEYS:
            return False
        player = self.game_view.player_sprite
        axis, sign, direction = _MOVE_KEYS[key]
        setattr(player, f"change_{axis}", sign * MOVEMENT_SPEED)
        player.direction = direction
        self._keys_held.add(key)
        return True

    def reset_movement_on_release(self, key, modifiers) -> None:
        if self.game_view.auto_walk_active:
            return
        if key not in _MOVE_KEYS:
            return
        player = self.game_view.player_sprite
        axis, _, _ = _MOVE_KEYS[key]
        setattr(player, f"change_{axis}", 0)
        self._keys_held.discard(key)

        # Met à jour direction + sprite selon les touches encore enfoncées
        for held_key in _MOVE_KEYS:
            if held_key in self._keys_held:
                _, _, direction = _MOVE_KEYS[held_key]
                player.direction = direction
                player.texture   = player.textures[direction]
                return
        # Aucune touche de mouvement — sprite idle de la direction actuelle
        player.texture = player.textures[player.direction]

    def _reset_keys_held(self) -> None:
        """Réinitialise les touches tenues (ex: reprise de contrôle après auto-walk)."""
        self._keys_held.clear()

    def _to_reinit(self, key) -> None:
        gv = self.game_view
        is_moving = key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D)
        if not is_moving:
            return
        if gv.current_strategique:
            gv.current_strategique = None
        if gv.current_map_action:
            gv.current_map_action = None
        if gv.current_objet:
            gv.current_objet = None
            gv.character_manager.stop_up()
            gv.character_manager.player.reading = False
        if gv.current_collection:
            gv.current_collection = None
            gv.open_collection = False
            gv.character_manager.stop_up()
            gv.character_manager.player.reading = False

    def _up_stat(self, key) -> None:
        gv = self.game_view
        if gv.current_map_action and key == arcade.key.ENTER:
            gv.quest_manager.complete_map_action_objective(
                gv.current_map_action.objective_name
            )
            gv.current_map_action = None
            return
        if gv.current_objet and key == arcade.key.ENTER:
            gv.current_objet.utiliser(gv.player_sprite, gv.character_manager)
        elif gv.current_collection:
            if key == arcade.key.ENTER:
                if gv.open_collection:
                    livre = gv.current_collection.upStats[gv.current_index_upstat]
                    gv.character_manager.player.reading = True
                    livre.utiliser(gv.player_sprite, gv.character_manager)
                else:
                    gv.open_collection = True
            elif gv.open_collection:
                nb = len(gv.current_collection.upStats)
                if key == arcade.key.UP:
                    gv.current_index_upstat = (gv.current_index_upstat - 1) % nb
                elif key == arcade.key.DOWN:
                    gv.current_index_upstat = (gv.current_index_upstat + 1) % nb

    def _to_show_stat(self, key) -> None:
        if self.game_view.is_typing:
            return
        if key == arcade.key.P:
            self.game_view.window.show_view(StatsView(self.game_view))

    def _to_dialogue(self, key) -> bool:
        gv = self.game_view
        player = gv.player_sprite
        pnjs = gv.pnj_sprite
        if gv.is_typing:
            if key == arcade.key.ENTER:
                if gv.current_pnj and not gv.waiting_response:
                    gv.dialogue.request_response(gv.current_input, gv.current_pnj)
                gv.current_input = ""
            elif key == arcade.key.BACKSPACE:
                gv.current_input = gv.current_input[:-1]
            return True  # bloque tout le reste (mouvement, menus, etc.)
        if key == arcade.key.ENTER:
            for pnj in pnjs:
                if arcade.get_distance_between_sprites(player, pnj) < getattr(pnj, "interaction_distance", 60):
                    dx = player.center_x - pnj.center_x
                    dy = player.center_y - pnj.center_y
                    if abs(dx) > abs(dy):
                        pnj.texture = pnj.textures["right"] if dx > 0 else pnj.textures["left"]
                    else:
                        pnj.texture = pnj.textures["up"] if dy > 0 else pnj.textures["down"]
                    if pnj.nom == "Kyle" and self._kyle_cutscene_needed(gv):
                        gv.kyle_cutscene.open()
                        return True
                    if pnj.nom == "Sylvain" and self._cutscene_needed(gv, 2, 1, "Sylvain"):
                        gv.sylvain_cutscene.open()
                        return True
                    if pnj.nom == "Jean christophe" and self._cutscene_needed(gv, 2, 1, "Jean christophe"):
                        gv.jc_cutscene.open()
                        return True
                    if pnj.nom == "Guy" and self._cutscene_needed(gv, 2, 4, "Guy"):
                        gv.guy_cutscene.open()
                        return True
                    pnj.transition_to(PNJState.DIALOGUE)
                    gv.current_pnj = pnj
                    gv.is_typing = True
                    gv.current_input = ""
                    gv.quest_manager.complete_talk_objective(pnj.nom)
                    return True
        return False

    def _cutscene_needed(self, gv, arc_id: int, quest_id: int, pnj_name: str) -> bool:
        qm = gv.quest_manager
        if qm.arc is None or qm.arc.arc_id != arc_id:
            return False
        quest = next((q for q in qm.arc.quests if q.status == "ec" and q.id == quest_id), None)
        if quest is None:
            return False
        return any(
            o.type == "talk" and o.stat_key == pnj_name and o.status != "t"
            for o in quest.objectives
        )

    def _kyle_cutscene_needed(self, gv) -> bool:
        return self._cutscene_needed(gv, 3, 1, "Kyle")
