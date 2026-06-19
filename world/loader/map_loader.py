from __future__ import annotations
import json
from typing import TYPE_CHECKING
import arcade
from assets.param_map import PLAYER_SCALING
from character.pnj.pnj import PNJ
from character.pnj.pnj_loader import humain_from_data
from character.equipment.weapon import Weapon
from world.objects.up_stat import UpStat
from world.objects.up_stat_collection import UpStatCollection
from world.objects.map_action_object import MapActionObject
from world.objects.interactable import ObjetInteractif
import utils.paths as paths

if TYPE_CHECKING:
    from world.scene.base_scene import BaseScene


class MapLoader:
    """Lit le JSON de config d'une map et instancie PNJs / objets interactifs.

    Format JSON attendu :
        {
            "tilemap": "...",
            "player_spawn": { ... },
            "base": {
                "pnjs": [...],
                "strategiques": [...],
                "objets": [...]
            },
            "arc_1": { "pnjs": [...], "objets": [...] },
            "arc_2": { ... }
        }
    "base" est toujours chargé. Les sections arc_1 … arc_N sont fusionnées
    cumulativement (arc_1 persiste en arc_2, arc_2 persiste en arc_3, etc.).
    Rétro-compatible : si "base" est absent, lit pnjs/objets à la racine.
    """

    def __init__(self, map_name: str, arc_id: int | None = None):
        config_path = paths.asset(f"world/configs/{map_name}.json")
        with open(config_path, encoding="utf-8") as f:
            self._cfg = json.load(f)
        self._arc_id = arc_id

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

    def load_pnjs(self, game_view: "BaseScene",
                  behind_player: arcade.SpriteList | None = None) -> None:
        """Crée les PNJs normaux et les ajoute à game_view.pnj_sprite."""
        for data in self._get_section_data("pnjs"):
            pnj = self._make_pnj(data)
            pnj.interaction_distance = data.get("interaction_distance", 60)
            game_view.pnj_sprite.append(pnj)
            if data.get("behind_player") and behind_player is not None:
                behind_player.append(pnj)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, pnj)

    def load_strategiques(self, game_view: "BaseScene") -> None:
        """Crée les PNJs stratégiques et les ajoute à game_view.strategique_sprite."""
        for data in self._get_section_data("strategiques"):
            pnj = self._make_pnj(data)
            pnj.interaction_distance = data.get("interaction_distance", 50)
            game_view.strategique_sprite.append(pnj)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, pnj)

    def load_objets(self, game_view: "BaseScene") -> None:
        """Crée les objets interactifs et les ajoute à game_view.objet_sprites."""
        for data in self._get_section_data("objets"):
            objet = self._make_objet(data)
            if objet is None:
                continue
            game_view.objet_sprites.append(objet)
            layer = data.get("scene_layer")
            if layer:
                game_view.scene.add_sprite(layer, objet)

    # ------------------------------------------------------------------ private

    def _get_section_data(self, key: str) -> list:
        """Retourne les données de l'arc courant, ou de 'base' si pas d'arc actif."""
        if self._arc_id is not None:
            arc_key = f"arc_{self._arc_id}"
            if arc_key in self._cfg:
                return list(self._cfg[arc_key].get(key, []))
        return list(self._cfg.get("base", self._cfg).get(key, []))

    def _make_pnj(self, data: dict) -> PNJ:
        nom = data["nom"]
        pnj = PNJ(nom, humain_from_data(nom), data.get("genre", "Male"),
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

        # Textures de marche + stand (ex : Kyle qui marche comme le joueur)
        walk_prefix = data.get("walk_textures")
        if walk_prefix:
            pnj.load_walk_textures(walk_prefix)
            pnj._stand_textures = dict(pnj.textures)
            pnj._standing_tex   = pnj.textures["down"]

        # Texture assise fixe (remplace les 4 directions)
        sitting_img = data.get("sitting_image")
        if sitting_img:
            sitting_tex = arcade.load_texture(paths.asset(sitting_img))
            pnj._sitting_tex = sitting_tex
            pnj.textures = {d: sitting_tex for d in ("up", "down", "left", "right")}
            pnj.texture  = sitting_tex

        # Propriétés de combat
        if "speed" in data:
            pnj.speed = data["speed"]
        if "fire_interval" in data:
            pnj._fire_interval = data["fire_interval"]

        # Arme
        weapon_data = data.get("weapon")
        if weapon_data:
            color = tuple(weapon_data.get("bullet_color", [255, 210, 50]))
            pnj.weapon = Weapon(weapon_data["name"],
                                weapon_data["damage_min"],
                                weapon_data["damage_max"],
                                bullet_color=color)

        return pnj

    def _make_objet(self, data: dict):
        kind  = data["type"]
        image = paths.asset(data["image"])
        scale = data.get("scale", 1)
        x     = data.get("x", 0.0)
        y     = data.get("y", 0.0)

        if kind == "UpStat":
            return UpStat(image, scale, data["name"],
                          data["stat"], data.get("stat_min", 0), data.get("stat_max", 1),
                          x=x, y=y)

        if kind == "UpStatCollection":
            obj = UpStatCollection(image, scale, data["name"], x=x, y=y)
            for item in data.get("items", []):
                sub = UpStat(paths.asset(item["image"]), item.get("scale", 1),
                             item["name"], item["stat"],
                             item.get("stat_min", 0), item.get("stat_max", 1))
                obj.add_upStats(sub)
            return obj

        if kind == "MapActionObject":
            return MapActionObject(image, scale, data["name"], data["objective_name"],
                                   x=x, y=y)

        if kind == "ObjetInteractif":
            return ObjetInteractif(image, scale, data["name"], x=x, y=y)

        print(f"[MapLoader] Type d'objet inconnu : '{kind}'")
        return None
