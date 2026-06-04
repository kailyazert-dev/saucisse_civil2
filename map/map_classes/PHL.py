from __future__ import annotations
import arcade
from character.character_classes import Humain, PNJ
from assets.param_map import PLAYER_SCALING
from assets.param_humain import IbmI_personnage
from map.map_base import BaseGameView
from map.map_classes.objet import UpStat, MapActionObject
import utils.paths as paths


def _humain_from_data(name: str) -> Humain:
    """Crée un Humain avec les stats de param_humain pour ce PNJ."""
    d = IbmI_personnage.personnages.get(name, {})
    phys = d.get("competences", {}).get("physique", {})
    intel = d.get("competences", {}).get("intelecte", {})
    return Humain(
        charisme=d.get("charisme", 0.1),
        rigidite=d.get("rigidite", 0.1),
        beauf=d.get("intensite_boof", 0.1),
        receptif_beauf=d.get("receptif_boof", 0.1),
        force=phys.get("force", 0.1),
        vitesse=phys.get("vitesse", 0.1),
        endurance=phys.get("endurance", 0.1),
        mathematique=intel.get("mathematique", 0.1),
        logique=intel.get("logique", 0.1),
        rpg=0.1,
        music=intel.get("musique", 0.1),
        langue=intel.get("langage", 0.1),
        sociabilite=intel.get("sociale", 0.1),
    )


class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)
        self.quest_manager = quest_manager
        self.character_manager = character_manager

    def setup(self, last_map: str | None) -> None:
        try:
            self.tile_map = arcade.load_tilemap(paths.asset("map/map_tmx/PHL.tmx"), scaling=1.0)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger la carte PHL : {e}") from e

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        entry_positions = {
            "tma": (2792, 1848),
            "home": (574, 50),
        }
        x, y = entry_positions.get(last_map or "", (72, 72))

        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y
        self.scene.add_sprite("Player", self.player_sprite)

        # PNJs — chacun avec ses propres stats
        for nom, cx, cy in [
            ("Mael",   694, 940),
            ("Louis",  556, 940),
            ("Thomas", 556, 790),
            ("Kyle",   694, 790),
            ("Sylvain",       264, 529),
            ("Jean christophe", 165, 529),
        ]:
            pnj = PNJ(nom, _humain_from_data(nom), "Male", paths.asset("assets/images/player_d.png"), PLAYER_SCALING)
            pnj.center_x = cx
            pnj.center_y = cy
            self.pnj_sprite.append(pnj)
            self.scene.add_sprite("Pnj", pnj)

        hotesse = PNJ("Hotesse", _humain_from_data("Hotesse"), "Femelle", paths.asset("assets/images/hotesse_l.png"), PLAYER_SCALING)
        hotesse.center_x = 2850
        hotesse.center_y = 1848
        self.strategique_sprite.append(hotesse)
        self.scene.add_sprite("Pnj", hotesse)

        livre = UpStat(paths.asset("assets/images/livre.png"), 0.7, "Pythagore", "mathematique", 0, 0.3)
        livre.center_x = 448
        livre.center_y = 1030
        self.objet_sprites.append(livre)
        self.scene.add_sprite("Livre", livre)

        # Ordinateur RPG (arc 2, quest 2 : rpg 0 → 0.14)
        ordi_rpg = UpStat(paths.asset("assets/images/ordinateur.png"), 1, "Intro RPG", "rpg", 0, 0.14)
        ordi_rpg.center_x = 265
        ordi_rpg.center_y = 991
        self.objet_sprites.append(ordi_rpg)
        self.scene.add_sprite("OrdiRPG", ordi_rpg)

        # Même ordinateur — test de formation (arc 2, quest 3)
        pc_test = MapActionObject(paths.asset("assets/images/ordinateur.png"), 1, "Test de formation", "Valide le test de la formation.")
        pc_test.center_x = 265
        pc_test.center_y = 991
        self.objet_sprites.append(pc_test)
        self.scene.add_sprite("PcTest", pc_test)

        obstacles = self.interact.create_obstacles()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, obstacles)

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()

        self.interact.interact_obj_prg()
        self.interact.interact_pnj_strateg()
        self.interact.interact_pnj()

        if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
            left, top = self.interact.draw_interact_box()
            arcade.draw_text("RALT : Maison", left + 15, top - 30, arcade.color.LIGHT_GREEN, 14)

        self.camera_gui.use()
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
            self.manager.switch_map("tma")

        if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600 and key == arcade.key.RALT:
            self.character_manager.save_player()
            self.manager.switch_map("home")

    def on_key_release(self, key, modifiers) -> None:
        self.keycaps.reset_movement_on_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        self.keycaps.on_mouse_press(x, y, button, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.camera_sprites.match_window()
