from __future__ import annotations
from character.player.player import Player
from world.objects.drops.base_drop import BaseDrop

_IMAGE = "assets/images/conssomables/health.png"


class HealthDrop(BaseDrop):
    """Cœur lâché par un zombie mort. Restaure des points de vie."""

    SOIN = 2

    def __init__(self, x: float, y: float) -> None:
        super().__init__(_IMAGE, x, y)

    def ramasser(self, player) -> None:
        max_hp = Player.MAX_HEALTH + getattr(player, "max_health_bonus", 0)
        player.health = min(max_hp, player.health + self.SOIN)
