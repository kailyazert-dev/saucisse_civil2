from __future__ import annotations
import arcade
from typing import TYPE_CHECKING
from assets.param_map import MOVEMENT_SPEED
from character.character_classes import PNJState
from map.ui_menus import StatsView

if TYPE_CHECKING:
    from map.map_base import BaseGameView


class InputHandler:
    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view

    def on_mouse_press(self, x: float, y: float, button, modifiers) -> None:
        gv = self.game_view
        qx, qy = gv.quest_x, gv.quest_y
        qw, qh = gv.quest_width / 2, gv.quest_height / 2
        if qx - qw <= x <= qx + qw and qy - qh <= y <= qy + qh:
            gv.show_side_bar = not gv.show_side_bar

    def handle_key_press(self, key, modifiers) -> None:
        gv = self.game_view
        if key == arcade.key.ESCAPE:
            gv.show_menu = not gv.show_menu
            gv.menu.selected = 0
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
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = MOVEMENT_SPEED
            player.direction = "up"
        elif key == arcade.key.S:
            player.change_y = -MOVEMENT_SPEED
            player.direction = "down"
        elif key == arcade.key.Q:
            player.change_x = -MOVEMENT_SPEED
            player.direction = "left"
        elif key == arcade.key.D:
            player.change_x = MOVEMENT_SPEED
            player.direction = "right"
        else:
            return False
        return True

    def reset_movement_on_release(self, key, modifiers) -> None:
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = 0
            player.texture = player.textures["up"]
        elif key == arcade.key.S:
            player.change_y = 0
            player.texture = player.textures["down"]
        elif key == arcade.key.Q:
            player.change_x = 0
            player.texture = player.textures["left"]
        elif key == arcade.key.D:
            player.change_x = 0
            player.texture = player.textures["right"]

    def _to_reinit(self, key) -> None:
        gv = self.game_view
        is_moving = key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D)
        if not is_moving:
            return
        if gv.is_typing:
            gv.is_typing = False
            gv.last_response = ""
            gv.current_input = ""
            if gv.current_pnj is not None:
                gv.current_pnj.leave_dialogue()
            gv.current_pnj = None
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
                return True
            if key == arcade.key.BACKSPACE:
                gv.current_input = gv.current_input[:-1]
                return True
            return False
        if key == arcade.key.ENTER:
            for pnj in pnjs:
                if arcade.get_distance_between_sprites(player, pnj) < 90:
                    dx = player.center_x - pnj.center_x
                    dy = player.center_y - pnj.center_y
                    if abs(dx) > abs(dy):
                        pnj.texture = pnj.textures["right"] if dx > 0 else pnj.textures["left"]
                    else:
                        pnj.texture = pnj.textures["up"] if dy > 0 else pnj.textures["down"]
                    pnj.transition_to(PNJState.DIALOGUE)
                    gv.current_pnj = pnj
                    gv.is_typing = True
                    gv.current_input = ""
                    gv.quest_manager.complete_talk_objective(pnj.nom)
                    return True
        return False
