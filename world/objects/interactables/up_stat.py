from __future__ import annotations
from world.objects.interactables.base_object import Objet


class UpStat(Objet):
    def __init__(self, image_path: str, scale: float, name: str,
                 stat_cible: str, stat_min: float = 0, stat_max: float = 100,
                 x: float = 0.0, y: float = 0.0):
        super().__init__(image_path, scale, name, x, y)
        self.stat_cible = stat_cible
        self.stat_min   = stat_min
        self.stat_max   = stat_max

    def interact(self, player, character_manager, quest_manager) -> None:
        player_level_stat = getattr(player.humain, self.stat_cible)
        if self.stat_min <= player_level_stat < self.stat_max:
            character_manager.start_up(self)
