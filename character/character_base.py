"""Classe mère commune à tous les personnages du jeu (joueur, PNJ, ennemis)."""
from __future__ import annotations
import arcade
import utils.paths as paths
from character.equipment.weapon import Weapon  # noqa: F401
from character.equipment.bullet import Bullet  # noqa: F401


def _img(filename: str) -> str:
    return paths.asset(f"assets/images/{filename}")


_DIRS: dict[str, tuple[int, int]] = {
    "up":    (0,  1),
    "down":  (0, -1),
    "left":  (-1, 0),
    "right": (1,  0),
}


# ---------------------------------------------------------------------------
class Humain:
    """Stats d'un personnage humain (joueur ou PNJ)."""

    def __init__(self,
                 force:        float = 0.1,
                 vitesse:      float = 0.1,
                 endurance:    float = 0.1,
                 mathematique: float = 0.14,
                 logique:      float = 0.14,
                 rpg:          float = 0.1,
                 music:        float = 0.1,
                 langue:       float = 0.1,
                 sociabilite:  float = 0.1,
                 x:            float = 0.0,
                 y:            float = 0.0) -> None:
        self.force        = force
        self.vitesse      = vitesse
        self.endurance    = endurance
        self.mathematique = mathematique
        self.logique      = logique
        self.rpg          = rpg
        self.music        = music
        self.langue       = langue
        self.sociabilite  = sociabilite
        self.x, self.y    = x, y

    def get_stats_physique(self) -> list[tuple[str, float]]:
        return [("Force", self.force), ("Vitesse", self.vitesse), ("Endurance", self.endurance)]

    def get_stats_intellect(self) -> list[tuple[str, float]]:
        return [("Math", self.mathematique), ("Logique", self.logique), ("RPG", self.rpg)]

    def get_stats_sociale(self) -> list[tuple[str, float]]:
        return [("Musique", self.music), ("Langue", self.langue), ("Sociabilite", self.sociabilite)]


# ---------------------------------------------------------------------------
class CharacterBase(arcade.Sprite):
    """Classe mère de tous les personnages : joueur, PNJ, ennemis.

    Propriétés communes :
      - nom, humain (stats), direction
      - health, damage_cooldown, weapon
      - textures directionnelles (idle + marche)
      - face(), load_walk_textures(), _animate()
    """

    _DIRS        = _DIRS
    _WALK_SWITCH = 0.15

    def __init__(self, nom: str, humain: Humain,
                 image_path: str, scale: float = 1.0) -> None:
        super().__init__(image_path, scale)
        self.nom              = nom
        self.humain           = humain
        self.direction        = "down"
        self.health: int      = 100
        self.damage_cooldown  = 0.0
        self.weapon: Weapon | None = None

        self.textures: dict[str, arcade.Texture]                    = {}
        self.textures_walk: dict[str, list[arcade.Texture]] | None  = None
        self._walk_frame = 0
        self._walk_timer = 0.0

    # ---------------------------------------------------------------- public

    def get_nom(self) -> str:
        return self.nom

    def face(self, dx: float, dy: float) -> None:
        """Oriente le sprite vers la direction (dx, dy)."""
        key = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) \
              else ("up" if dy > 0 else "down")
        self.texture = self.textures[key]

    def load_walk_textures(self, prefix: str) -> None:
        """Charge textures idle et marche depuis assets/images/<prefix>_<d>.png."""
        self.textures = {
            d: arcade.load_texture(_img(f"{prefix}_{d[0]}.png"))
            for d in self._DIRS
        }
        self.textures_walk = {
            d: [arcade.load_texture(_img(f"{prefix}_{d[0]}1.png")),
                arcade.load_texture(_img(f"{prefix}_{d[0]}2.png"))]
            for d in self._DIRS
        }

    # ---------------------------------------------------------------- private

    def _animate(self, direction: str, dt: float) -> None:
        """Alterne les frames de marche selon le timer."""
        self._walk_timer += dt
        if self._walk_timer >= self._WALK_SWITCH:
            self._walk_frame = 1 - self._walk_frame
            self._walk_timer = 0.0
        if self.textures_walk:
            self.texture = self.textures_walk[direction][self._walk_frame]
        else:
            self.texture = self.textures.get(direction, self.texture)
