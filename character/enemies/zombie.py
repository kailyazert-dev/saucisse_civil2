from __future__ import annotations
import math
import random
import arcade
import utils.paths as paths
from character.character_base import CharacterBase, Humain

_CHASE_RADIUS    = 220
_CHASE_EXIT      = 450
_WANDER_SPEED    = 90.0
_CHASE_SPEED_MAX = 125.0
_CHASE_ACCEL     = 30.0
_WANDER_CHANGE   = (2.5, 4.5)


def _img(filename: str) -> str:
    return paths.asset(f"assets/images/{filename}")


class Zombie(CharacterBase):
    MAX_HEALTH   = 3
    DAMAGE       = 2
    _WALK_SWITCH = 0.2

    def __init__(self, x: float, y: float):
        super().__init__("Zombie", Humain(), _img("z_d.png"))
        self.scale    = 1.2
        self.center_x = x
        self.center_y = y
        self.health   = self.MAX_HEALTH
        self._chasing      = False
        self._speed        = _WANDER_SPEED
        self._wander_dir   = random.uniform(0, math.pi * 2)
        self._wander_timer = 0.0
        self._wander_next  = random.uniform(*_WANDER_CHANGE)

        self.load_walk_textures("z")

    def move(self, player: arcade.Sprite, dt: float,
             walls: arcade.SpriteList | None) -> None:
        dist = math.hypot(player.center_x - self.center_x,
                          player.center_y - self.center_y)
        if dist < _CHASE_RADIUS:
            self._chasing = True
        elif dist > _CHASE_EXIT:
            self._chasing = False

        if self._chasing:
            self._speed = min(_CHASE_SPEED_MAX, self._speed + _CHASE_ACCEL * dt)
            self._chase(player, dt, walls)
        else:
            self._speed = _WANDER_SPEED
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
            self._wander_next  = random.uniform(*_WANDER_CHANGE)
            self._wander_timer = 0.0

        nx = math.cos(self._wander_dir)
        ny = math.sin(self._wander_dir)
        self._set_direction(nx, ny)
        step = _WANDER_SPEED * dt
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
