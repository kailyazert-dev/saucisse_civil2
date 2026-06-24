from __future__ import annotations
import arcade


class Objet(arcade.Sprite):
    """Classe de base pour tous les objets interactifs placés sur la map."""

    def __init__(self, image_path: str, scale: float, name: str = "",
                 x: float = 0.0, y: float = 0.0):
        super().__init__(image_path, scale)
        self.name = name
        self.center_x = x
        self.center_y = y

    def get_name(self) -> str:
        return self.name

    def interact(self, player, character_manager, quest_manager) -> None:
        """Déclenché au ENTER du joueur. Surcharger dans les sous-classes."""
        pass

    def is_available(self, quest_manager) -> bool:
        """True si l'objet est actif et peut être interagi."""
        return True
