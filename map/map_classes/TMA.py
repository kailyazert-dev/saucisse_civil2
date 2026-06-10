from __future__ import annotations
import arcade
from character.character_classes import Humain, PNJ
from assets.param_map import PLAYER_SCALING
from assets.param_humain import IbmI_personnage
from map.map_base import BaseGameView
from map.map_classes.objet import UpStat
import utils.paths as paths


class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)
        self.quest_manager = quest_manager
        self.character_manager = character_manager

    def setup(self, last_map: str | None) -> None:
        try:
            self.tile_map = arcade.load_tilemap(paths.asset("map/map_tmx/TMA.tmx"), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte TMA : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x = 1300
        self.player_sprite.center_y = 1225
        self.scene.add_sprite("Player", self.player_sprite)

        d = IbmI_personnage.personnages.get("Hotesse", {})
        hotesse_humain = Humain(charisme=d.get("charisme", 0.5), rigidite=d.get("rigidite", 0.8))
        hotesse = PNJ("Hotesse", hotesse_humain, "Femelle", paths.asset("assets/images/hotesse_d.png"), PLAYER_SCALING)
        hotesse.center_x = 1360
        hotesse.center_y = 1220
        self.strategique_sprite.append(hotesse)
        self.scene.add_sprite("Pnj", hotesse)

        # Directeur (arc 3, quest 1 : parler à Guy)
        d_guy = IbmI_personnage.personnages.get("Guy", {})
        guy_humain = Humain(charisme=d_guy.get("charisme", 0.9), rigidite=d_guy.get("rigidite", 0.9))
        guy = PNJ("Guy", guy_humain, "Male", paths.asset("assets/images/player_d.png"), PLAYER_SCALING)
        guy.center_x = 2830
        guy.center_y = 660
        self.pnj_sprite.append(guy)
        self.scene.add_sprite("Pnj", guy)

        obstacles = self.interact.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()
        self.interact.interact_obj_prg()
        self.interact.interact_pnj_strateg()
        self.interact.interact_pnj()
        self.draw_stat_progress_bar()
        self.camera_gui.use()
        self.talk.draw_dialogue_box()
        self.interact.draw_box()
        self.get_quests()
        self.interact.draw_side_bar()
        self.get_position()
        self.draw_notif()
        self.menu.draw()

    def on_text(self, text: str) -> None:
        if self.is_typing:
            self.talk.on_text(text)

    def on_update(self, delta_time: float) -> None:
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)

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
