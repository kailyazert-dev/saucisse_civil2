from __future__ import annotations
from world.objects.base_object import Objet


class MapActionObject(Objet):
    """Objet lié à un objectif de type map_action."""

    def __init__(self, image_path: str, scale: float, name: str,
                 objective_name: str, x: float = 0.0, y: float = 0.0):
        super().__init__(image_path, scale, name, x, y)
        self.objective_name = objective_name

    def interact(self, player, character_manager, quest_manager) -> None:
        if quest_manager:
            quest_manager.complete_map_action_objective(self.objective_name)

    def is_available(self, quest_manager) -> bool:
        if quest_manager is None or quest_manager.arc is None:
            return False
        for quest in quest_manager.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if (obj.type in ("map_action", "test")
                        and obj.name == self.objective_name
                        and obj.status != "t"):
                    return True
        return False
