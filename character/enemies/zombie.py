from __future__ import annotations
import math
import random
import arcade
import utils.paths as paths
from character.character_base import CharacterBase, Humain


class Zombie(CharacterBase):
    MAX_HEALTH      = 3
    DAMAGE          = 2
    _WALK_SWITCH    = 0.2

    # Paramètres de mouvement — surchargeables dans les sous-classes
    VITESSE_ERRANCE = 90.0
    VITESSE_CHASSE  = 125.0
    ACCEL_CHASSE    = 30.0
    RAYON_DETECTION = 220
    RAYON_FUITE     = 450
    CHANGEMENT_DIR  = (2.5, 4.5)

    # Préfixe des sprites (chemin relatif à assets/images/) — surcharger dans les sous-classes
    _SPRITE_PREFIX = "enemies/zombies/z_1"

    # None = lazy-load par défaut, [] = aucun drop, [...] = drops explicites
    _DROPS: list | None = None

    # ---------------------------------------------------------------- drops

    @classmethod
    def _get_drops_config(cls) -> list[tuple[type, float]]:
        if cls._DROPS is None:
            from world.objects.drops.gold_drop import GoldDrop
            from world.objects.drops.health_drop import HealthDrop
            cls._DROPS = [(GoldDrop, 0.65), (HealthDrop, 0.20)]
        return cls._DROPS

    @classmethod
    def loot(cls, x: float, y: float) -> list:
        """Génère les drops à la position de mort selon les probabilités de la classe."""
        return [
            Drop(x, y)
            for Drop, chance in cls._get_drops_config()
            if random.random() < chance
        ]

    # ---------------------------------------------------------------- init

    def __init__(self, x: float, y: float):
        super().__init__("Zombie", Humain(), paths.asset(f"assets/images/{self._SPRITE_PREFIX}_d.png"))
        self.scale    = 1.2
        self.center_x = x
        self.center_y = y
        self.health   = self.MAX_HEALTH
        self._chasing      = False
        self._speed        = self.VITESSE_ERRANCE
        self._wander_dir   = random.uniform(0, math.pi * 2)
        self._wander_timer = 0.0
        self._wander_next  = random.uniform(*self.CHANGEMENT_DIR)

        self.load_walk_textures(self._SPRITE_PREFIX)

    # ---------------------------------------------------------------- mouvement

    def move(self, player: arcade.Sprite, dt: float,
             walls: arcade.SpriteList | None) -> None:
        dist = math.hypot(player.center_x - self.center_x,
                          player.center_y - self.center_y)
        if dist < self.RAYON_DETECTION:
            self._chasing = True
        elif dist > self.RAYON_FUITE:
            self._chasing = False

        if self._chasing:
            self._speed = min(self.VITESSE_CHASSE, self._speed + self.ACCEL_CHASSE * dt)
            self._chase(player, dt, walls)
        else:
            self._speed = self.VITESSE_ERRANCE
            self._wander(dt, walls)

        self._animate(self.direction, dt)

    def _set_direction(self, dx: float, dy: float) -> None:
        if abs(dx) >= abs(dy):
            self.direction = "right" if dx > 0 else "left"
        else:
            self.direction = "up" if dy > 0 else "down"

    def _chase(self, player: arcade.Sprite, dt: float,
               walls: arcade.SpriteList | None) -> None:
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        self._set_direction(dx, dy)
        self._slide(dx / dist, dy / dist, self._speed * dt, walls)

    def _wander(self, dt: float, walls: arcade.SpriteList | None) -> None:
        self._wander_timer += dt
        if self._wander_timer >= self._wander_next:
            self._wander_dir   = random.uniform(0, math.pi * 2)
            self._wander_next  = random.uniform(*self.CHANGEMENT_DIR)
            self._wander_timer = 0.0

        nx = math.cos(self._wander_dir)
        ny = math.sin(self._wander_dir)
        self._set_direction(nx, ny)
        step = self.VITESSE_ERRANCE * dt
        ox, oy = self.center_x, self.center_y

        self.center_x = ox + nx * step
        self.center_y = oy + ny * step
        if self.center_y < 28:
            self.center_y = 28
            self._wander_dir = random.uniform(math.pi * 0.1, math.pi * 0.9)
        if walls and arcade.check_for_collision_with_list(self, walls):
            self.center_x, self.center_y = ox, oy
            self._wander_dir   = random.uniform(0, math.pi * 2)
            self._wander_timer = 0.0

    def _slide(self, nx: float, ny: float, step: float,
               walls: arcade.SpriteList | None) -> None:
        ox, oy = self.center_x, self.center_y
        for mx, my in [(nx, ny), (nx, 0), (0, ny)]:
            self.center_x = ox + mx * step
            self.center_y = oy + my * step
            if walls is None or not arcade.check_for_collision_with_list(self, walls):
                return
        self.center_x, self.center_y = ox, oy
