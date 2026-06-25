from __future__ import annotations
import math
import arcade


class Bullet(arcade.SpriteSolidColor):
    """Projectile tiré par n'importe quel personnage."""

    SPEED    = 10.0
    LIFETIME = 90

    def __init__(self, x: float, y: float, tx: float, ty: float,
                 damage: float = 1.0,
                 color: tuple[int, int, int] = (255, 210, 50),
                 speed: float | None = None,
                 size: int = 8) -> None:
        super().__init__(size, size, arcade.color.WHITE)
        self.color = (*color, 255) if len(color) == 3 else color
        self.center_x, self.center_y = x, y
        self.damage = damage
        _speed = speed if speed is not None else self.SPEED
        dist = math.hypot(tx - x, ty - y)
        if dist > 0:
            self.vel_x = (tx - x) / dist * _speed
            self.vel_y = (ty - y) / dist * _speed
        else:
            self.vel_x = self.vel_y = 0.0
        self.life = self.LIFETIME

    def step(self) -> None:
        self.center_x += self.vel_x
        self.center_y += self.vel_y
        self.life -= 1
