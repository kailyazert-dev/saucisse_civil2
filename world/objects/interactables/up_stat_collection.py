from __future__ import annotations
from world.objects.interactables.base_object import Objet


class UpStatCollection(Objet):
    """Conteneur de plusieurs UpStat (ex : bibliothèque avec plusieurs livres)."""

    def __init__(self, image_path: str, scale: float, name: str,
                 x: float = 0.0, y: float = 0.0):
        super().__init__(image_path, scale, name, x, y)
        self.upStats = []

    def add_upStats(self, upstat) -> None:
        self.upStats.append(upstat)

    def remove_upStats(self, upstat) -> None:
        self.upStats.remove(upstat)

    def get_all_upStats(self) -> list:
        return self.upStats
