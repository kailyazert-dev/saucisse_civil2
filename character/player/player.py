from __future__ import annotations
from typing import TYPE_CHECKING
import arcade
from assets.param_map import PLAYER_SCALING
import utils.paths as paths
from character.character_base import CharacterBase, Humain
from character.equipment.weapon import Weapon  # noqa: F401

if TYPE_CHECKING:
    from quests.quest_manager import QuestManager
    from character.player.player_manager import CharacterManager


def _img(filename: str) -> str:
    return paths.asset(f"assets/images/{filename}")


class Player(CharacterBase):
    MAX_HEALTH     = 5
    DAMAGE_COOLDOWN = 1     # Temps entre chaque coup pour que des damage soit effectif

    def __init__(self, humain: Humain, nom: str, image_file: str,
                 quest_manager: "QuestManager", character_manager: "CharacterManager",
                 scale: float = PLAYER_SCALING) -> None:
        super().__init__(nom, humain, image_file, scale)
        self.reading           = False
        self.quest_manager     = quest_manager
        self.character_manager = character_manager
        self.health            = self.MAX_HEALTH
        self.weapon_feu:   Weapon | None = None
        self.weapon_blanc: Weapon | None = None

        self.textures = {
            "up":    arcade.load_texture(_img("player_u.png")),
            "down":  arcade.load_texture(_img("player_d.png")),
            "left":  arcade.load_texture(_img("player_l.png")),
            "right": arcade.load_texture(_img("player_r.png")),
            "read":  arcade.load_texture(_img("player_read1.png")),
        }
        self.textures_walk = {
            "up":    [arcade.load_texture(_img("player_u1.png")), arcade.load_texture(_img("player_u2.png"))],
            "down":  [arcade.load_texture(_img("player_d1.png")), arcade.load_texture(_img("player_d2.png"))],
            "left":  [arcade.load_texture(_img("player_l1.png")), arcade.load_texture(_img("player_l2.png"))],
            "right": [arcade.load_texture(_img("player_r1.png")), arcade.load_texture(_img("player_r2.png"))],
        }
        self.textures_read: list[arcade.Texture] = [
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read2.png")),
            arcade.load_texture(_img("player_read3.png")),
            arcade.load_texture(_img("player_read4.png")),
            arcade.load_texture(_img("player_read1.png")),
            arcade.load_texture(_img("player_read1.png")),
        ]
        self.read_texture_index:              int   = 0
        self.time_since_last_texture_change:  float = 0.0
        self.walking_texture_switch_interval: float = 0.2
        self.reading_texture_switch_interval: float = 0.5

    def update(self, delta_time: float = 1 / 60) -> None:
        self.character_manager.update_player_stats(delta_time)
        self.character_manager.animation.update(delta_time)
