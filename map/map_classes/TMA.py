from __future__ import annotations
import arcade
import os
from character.character_classes import Humain, PNJ
from assets.param_map import PLAYER_SCALING
from assets.param_humain import IbmI_personnage
from map.map_base import BaseGameView


class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)
        self.quest_manager = quest_manager
        self.character_manager = character_manager

    def setup(self, last_map: str | None) -> None:
        map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../map_tmx/TMA.tmx")
        try:
            self.tile_map = arcade.load_tilemap(map_path, scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte TMA : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x = 1300
        self.player_sprite.center_y = 1225
        self.scene.add_sprite("Player", self.player_sprite)

        d = IbmI_personnage.personnages.get("Hotesse", {})
        hotesse_humain = Humain(
            charisme=d.get("charisme", 0.5),
            rigidite=d.get("rigidite", 0.8),
        )
        hotesse = PNJ("Hotesse", hotesse_humain, "Femelle", "assets/images/hotesse_d.png", PLAYER_SCALING)
        hotesse.center_x = 1360
        hotesse.center_y = 1220
        self.strategique_sprite.append(hotesse)
        self.scene.add_sprite("Pnj", hotesse)

        obstacles = self.interact.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()
        self.interact.interact_obj_prg()
        self.interact.interact_pnj_strateg()
        self.interact.interact_pnj()
        self.camera_gui.use()
        self.interact.draw_box()
        self.get_quests()
        self.interact.draw_side_bar()

    def on_text(self, text: str) -> None:
        if self.is_typing:
            self.talk.on_text(text)

    def on_update(self, delta_time: float) -> None:
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()

    def on_key_press(self, key, modifiers) -> None:
        self.keycaps.handle_key_press(key, modifiers)
        if self.current_strategique and key == arcade.key.RALT:
            self.character_manager.save_player()
            self.manager.switch_map("phl")

    def on_key_release(self, key, modifiers) -> None:
        self.keycaps.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        self.keycaps.on_mouse_press(x, y, button, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.camera_sprites.match_window()
