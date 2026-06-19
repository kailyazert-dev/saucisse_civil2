from __future__ import annotations
import random
import utils.paths as paths


class Weapon:
    """Arme équipable par n'importe quel personnage."""

    def __init__(self, name: str, damage_min: float, damage_max: float,
                 bullet_color: tuple[int, int, int] = (255, 210, 50)) -> None:
        self.name         = name
        self.damage_min   = damage_min
        self.damage_max   = damage_max
        self.bullet_color = bullet_color
        self.image_path   = paths.asset(f"assets/images/weapons/{name}.png")

    def get_damage(self) -> float:
        return random.uniform(self.damage_min, self.damage_max)

    def __repr__(self) -> str:
        return f"<Weapon {self.name} [{self.damage_min}-{self.damage_max}]>"
