from __future__ import annotations
import json
import math
import random
import utils.paths as paths

_registry: dict | None = None

def _get_registry() -> dict:
    global _registry
    if _registry is None:
        with open(paths.asset("character/equipment/weapons.json"), encoding="utf-8") as f:
            _registry = json.load(f)
    return _registry


class Weapon:
    """Classe mère commune à toutes les armes."""
    weapon_type = "base"

    def __init__(self, name: str, damage_min: float, damage_max: float,
                 fire_interval: float = 0.2,
                 sprite_size: int | None = None) -> None:
        self.name          = name
        self.damage_min    = damage_min
        self.damage_max    = damage_max
        self.fire_interval = fire_interval
        self.sprite_size   = sprite_size
        self.image_path    = paths.asset(f"assets/images/weapons/{name}.png")
        self._texture       = None
        self._texture_tried = False

    def get_texture(self):
        """Charge le sprite de l'arme (lazy). Retourne None si le PNG est absent."""
        if not self._texture_tried:
            self._texture_tried = True
            try:
                import arcade
                self._texture = arcade.load_texture(self.image_path)
            except Exception:
                pass
        return self._texture

    @classmethod
    def from_name(cls, name: str) -> "Weapon":
        """Charge une arme depuis le registre weapons.json et retourne la sous-classe adaptée."""
        data = _get_registry()[name]
        wtype = data.get("type", "feu")
        if wtype == "feu":
            return FirearmWeapon(
                data["name"],
                data["damage_min"],
                data["damage_max"],
                bullet_color=tuple(data.get("bullet_color", [255, 210, 50])),
                fire_interval=data.get("fire_interval", 0.2),
                sprite_size=data.get("sprite_size", None),
            )
        if wtype == "blanc":
            return MeleeWeapon(
                data["name"],
                data["damage_min"],
                data["damage_max"],
                attack_radius=data.get("attack_radius", 80.0),
                half_span=data.get("half_span", 45.0),
                arc_color=tuple(data.get("arc_color", [255, 255, 255])),
                fire_interval=data.get("fire_interval", 0.4),
                sprite_size=data.get("sprite_size", None),
            )
        raise ValueError(f"Type d'arme inconnu : '{wtype}'")

    def use(self, player, zombie_manager, world_x: float, world_y: float,
            spawn_x: float | None = None, spawn_y: float | None = None) -> tuple[int, dict | None]:
        """Utilise l'arme. Retourne (kills, arc_dict | None)."""
        return 0, None

    def get_damage(self) -> float:
        return random.uniform(self.damage_min, self.damage_max)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} [{self.damage_min}-{self.damage_max}]>"


class FirearmWeapon(Weapon):
    """Arme à feu — tire des projectiles (Bullet)."""
    weapon_type = "feu"

    def __init__(self, name: str, damage_min: float, damage_max: float,
                 bullet_color: tuple[int, int, int] = (255, 210, 50),
                 fire_interval: float = 0.2,
                 sprite_size: int | None = None) -> None:
        super().__init__(name, damage_min, damage_max, fire_interval, sprite_size)
        self.bullet_color = bullet_color

    def use(self, player, zombie_manager, world_x: float, world_y: float,
            spawn_x: float | None = None, spawn_y: float | None = None) -> tuple[int, dict | None]:
        bx = spawn_x if spawn_x is not None else player.center_x
        by = spawn_y if spawn_y is not None else player.center_y
        zombie_manager.fire(bx, by, world_x, world_y, weapon=self)
        return 0, None


class MeleeWeapon(Weapon):
    """Arme blanche — inflige des dégâts dans un secteur autour du personnage."""
    weapon_type = "blanc"

    _ARC_DURATION = 0.20

    def __init__(self, name: str, damage_min: float, damage_max: float,
                 attack_radius: float = 80.0, half_span: float = 45.0,
                 arc_color: tuple = (255, 255, 255),
                 fire_interval: float = 0.4,
                 sprite_size: int | None = None) -> None:
        super().__init__(name, damage_min, damage_max, fire_interval, sprite_size)
        self.attack_radius = attack_radius
        self.half_span     = half_span
        self.arc_color     = arc_color

    def use(self, player, zombie_manager, world_x: float, world_y: float) -> tuple[int, dict | None]:
        angle = math.degrees(math.atan2(
            world_y - player.center_y, world_x - player.center_x))
        kills = zombie_manager.melee_attack(
            player, self.attack_radius, self.get_damage,
            attack_angle=angle, half_span=self.half_span)
        texture = self.get_texture()
        arc = {
            "cx": player.center_x, "cy": player.center_y,
            "angle": angle, "radius": self.attack_radius,
            "half_span": self.half_span,
            "arc_color": self.arc_color,
            "timer": self._ARC_DURATION, "max_timer": self._ARC_DURATION,
            "texture": texture,
            "sprite_size": self.sprite_size or (
                max(texture.width, texture.height) if texture else None),
        }
        return kills, arc
