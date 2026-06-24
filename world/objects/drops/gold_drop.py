from __future__ import annotations
import random
from world.objects.drops.base_drop import BaseDrop

_IMAGE = "assets/images/conssomables/coins.png"


class GoldDrop(BaseDrop):
    """Pièce d'or lâchée par un zombie mort."""

    VALEUR_MIN  = 1
    VALEUR_MAX  = 3

    def __init__(self, x: float, y: float) -> None:
        super().__init__(_IMAGE, x, y)
        self.valeur = random.randint(self.VALEUR_MIN, self.VALEUR_MAX)

    def ramasser(self, player) -> None:
        player.gold += self.valeur
