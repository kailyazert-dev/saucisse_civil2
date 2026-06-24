from __future__ import annotations
import arcade
import utils.paths as paths


class BaseDrop(arcade.Sprite):
    """Classe mère pour tous les objets lâchés par les zombies."""

    ECHELLE : float = 1

    def __init__(self, image: str, x: float, y: float) -> None:
        super().__init__(paths.asset(image), self.ECHELLE)
        self.center_x = x
        self.center_y = y

    def ramasser(self, player) -> None:
        """Applique l'effet du drop au joueur. Surcharger dans les sous-classes."""
        raise NotImplementedError
