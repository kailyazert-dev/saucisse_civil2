from __future__ import annotations
import json
from typing import TYPE_CHECKING
import arcade
from assets.param_map import PLAYER_SCALING
from assets.param_humain import IbmI_personnage
from character.character_classes import Humain, PNJ
from map.map_classes.objet import UpStat, UpStatCollection, MapActionObject
import utils.paths as paths

if TYPE_CHECKING:
    from map.map_base import BaseGameView


def humain_from_data(nom: str) -> Humain:
    """Construit un Humain à partir des données de param_humain.py."""
    d     = IbmI_personnage.personnages.get(nom, {})
    phys  = d.get("competences", {}).get("physique", {})
    intel = d.get("competences", {}).get("intelecte", {})
    return Humain(
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


class MapLoader:
    """Lit le JSON de config d'une map et instancie PNJs / objets interactifs."""

    def __init__(self, map_name: str):
        config_path = paths.asset(f"map/map_configs/{map_name}.json")
        with open(config_path, encoding="utf-8") as f:
            self._cfg = json.load(f)

    # ------------------------------------------------------------------ public

    def get_tilemap_path(self) -> str:
        return self._cfg["tilemap"]

    def get_player_spawn(self, from_map: str | None) -> tuple[float, float]:
        spawns = self._cfg.get("player_spawn", {})
        if from_map and from_map in spawns:
            pos = spawns[from_map]
        else:
            pos = spawns.get("default", [72, 72])
        return float(pos[0]), float(pos[1])

    def load_pnjs(self, game_view: BaseGameView,
                  behind_player: arcade.SpriteList | None = None) -> None:
        """Crée les PNJs normaux et les ajoute à game_view.pnj_sprite."""
        for data in self._cfg.get("pnjs", []):
            pnj = self._make_pnj(data)
            game_view.pnj_sprite.append(pnj)
            if data.get("behind_player") and behind_player is not None:
                behind_player.append(pnj)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, pnj)

    def load_strategiques(self, game_view: BaseGameView) -> None:
        """Crée les PNJs stratégiques et les ajoute à game_view.strategique_sprite."""
        for data in self._cfg.get("strategiques", []):
            pnj = self._make_pnj(data)
            pnj.interaction_distance = data.get("interaction_distance", 50)
            game_view.strategique_sprite.append(pnj)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, pnj)

    def load_objets(self, game_view: BaseGameView) -> None:
        """Crée les objets interactifs et les ajoute à game_view.objet_sprites."""
        for data in self._cfg.get("objets", []):
            objet = self._make_objet(data)
            if objet is None:
                continue
            game_view.objet_sprites.append(objet)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, objet)

    # ------------------------------------------------------------------ private

    def _make_pnj(self, data: dict) -> PNJ:
        nom    = data["nom"]
        pnj    = PNJ(nom, humain_from_data(nom), data.get("genre", "Male"),
                     paths.asset(data["image"]), PLAYER_SCALING,
                     attitude=data.get("attitude", "errance"))
        pnj.center_x = data["x"]
        pnj.center_y = data["y"]

        # Hitbox réduite à la moitié supérieure (PNJs debout derrière un comptoir)
        if data.get("hitbox") == "upper_half":
            tw, th = pnj.texture.width / 2, pnj.texture.height / 2
            pnj.hit_box = arcade.hitbox.RotatableHitBox(
                [(-tw, 0), (tw, 0), (tw, th), (-tw, th)],
                position=pnj.position, angle=pnj.angle,
            )

        # Texture assise fixe (remplace les 4 directions)
        sitting_img = data.get("sitting_image")
        if sitting_img:
            sitting_tex = arcade.load_texture(paths.asset(sitting_img))
            pnj.textures = {d: sitting_tex for d in ("up", "down", "left", "right")}
            pnj.texture  = sitting_tex

        return pnj

    def _make_objet(self, data: dict):
        kind  = data["type"]
        image = paths.asset(data["image"])
        scale = data.get("scale", 1)
        x, y  = data["x"], data["y"]

        if kind == "UpStat":
            obj = UpStat(image, scale, data["name"],
                         data["stat"], data.get("stat_min", 0), data.get("stat_max", 1))
            obj.center_x, obj.center_y = x, y
            return obj

        if kind == "UpStatCollection":
            obj = UpStatCollection(image, scale, data["name"])
            obj.center_x, obj.center_y = x, y
            for item in data.get("items", []):
                sub = UpStat(paths.asset(item["image"]), item.get("scale", 1),
                             item["name"], item["stat"],
                             item.get("stat_min", 0), item.get("stat_max", 1))
                obj.add_upStats(sub)
            return obj

        if kind == "MapActionObject":
            obj = MapActionObject(image, scale, data["name"], data["objective_name"])
            obj.center_x, obj.center_y = x, y
            return obj

        print(f"[MapLoader] Type d'objet inconnu : '{kind}'")
        return None
