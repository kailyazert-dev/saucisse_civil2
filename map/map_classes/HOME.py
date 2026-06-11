from __future__ import annotations
import arcade
from assets.param_map import KENNY, WINDOW_WIDTH, WINDOW_HEIGHT
from map.map_base import BaseGameView
from map.map_loader import MapLoader
import utils.paths as paths


class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)

    def setup(self, last_map):
        loader = MapLoader("HOME")

        self.tile_map = arcade.load_tilemap(paths.asset(loader.get_tilemap_path()), scaling=1.0)
        self.scene    = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x, self.player_sprite.center_y = loader.get_player_spawn(last_map)
        self.scene.add_sprite("Player", self.player_sprite)

        loader.load_pnjs(self)
        loader.load_strategiques(self)
        loader.load_objets(self)

        obstacles = self.interact_ui.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

        self._fade_alpha = 0
        self._fade_dir   = 0  # 0=idle  1=assombrir  -1=éclaircir

    # ---------------------------------------------------------------- logique HOME

    def _sleep_available(self) -> bool:
        if self.quest_manager.arc is None:
            return False
        for quest in self.quest_manager.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type == "map_action" and obj.name == "Home sweet home." and obj.status != "t":
                    return True
        return False

    def _near_bed(self) -> bool:
        return (1150 <= self.player_sprite.center_x <= 1200
                and 290 <= self.player_sprite.center_y <= 340)

    @property
    def _phl_unlocked(self) -> bool:
        arc = self.quest_manager.arc
        if arc is None:
            return True  # Plus d'arcs = jeu terminé, accès libre
        return arc.arc_id >= 2

    # ---------------------------------------------------------------- draw

    def on_draw(self):
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()

        self.interact_ui.interact_obj_prg()
        self.interact_ui.interact_pnj_strateg()
        self.interact_ui.interact_pnj()

        if self._phl_unlocked:
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750:
                left, top = self.interact_ui.draw_interact_box()
                cx = left + (self.interact_ui._BOX_W - 10) / 2
                cy = top - self.interact_ui._BOX_H / 2
                arcade.draw_text("Sortie", cx, cy + 9, arcade.color.ORANGE, 13,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)
                arcade.draw_text("[Entrée] PHL", cx, cy - 9, self.interact_ui._HINT_COL, 11,
                                 anchor_x="center", anchor_y="center", font_name=KENNY)

        if self._sleep_available() and self._near_bed() and self._fade_dir == 0:
            left, top = self.interact_ui.draw_interact_box()
            cx = left + (self.interact_ui._BOX_W - 10) / 2
            cy = top - self.interact_ui._BOX_H / 2
            arcade.draw_text("Lit", cx, cy + 9, arcade.color.ORANGE, 13,
                             anchor_x="center", anchor_y="center", font_name=KENNY)
            arcade.draw_text("[Entrée] Dormir", cx, cy - 9, self.interact_ui._HINT_COL, 11,
                             anchor_x="center", anchor_y="center", font_name=KENNY)

        self.draw_stat_progress_bar()

        self.camera_gui.use()

        if self._fade_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, (0, 0, 0, self._fade_alpha))

        self.dialogue.draw_dialogue_box()
        self.interact_ui.draw_box()
        self.get_quests()
        self.interact_ui.draw_side_bar()
        self.get_position()
        self.draw_notif()
        self.menu.draw()

    # ---------------------------------------------------------------- update

    def on_update(self, delta_time):
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)
        self.character_manager.update_player_stats(delta_time)

        _SPEED = 5
        if self._fade_dir == 1:
            self._fade_alpha = min(255, self._fade_alpha + _SPEED)
            if self._fade_alpha >= 255:
                self.quest_manager.complete_map_action_objective("Home sweet home.")
                self.character_manager.save_player()
                self._fade_dir = -1
        elif self._fade_dir == -1:
            self._fade_alpha = max(0, self._fade_alpha - _SPEED)
            if self._fade_alpha <= 0:
                self._fade_dir = 0

    # ---------------------------------------------------------------- input

    def on_text(self, text):
        if self.is_typing:
            self.dialogue.on_text(text)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        self.input_handler.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, key, modifiers):
        if self._fade_dir != 0:
            return
        if key == arcade.key.ENTER and self._sleep_available() and self._near_bed():
            self._fade_dir = 1
            return
        self.input_handler.handle_key_press(key, modifiers)
        if self._phl_unlocked and not self.is_typing:
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750 and key == arcade.key.ENTER:
                self.character_manager.save_player()
                self.manager.switch_map("phl")

    def on_key_release(self, key, modifiers):
        self.input_handler.reset_movement_on_release(key, modifiers)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
