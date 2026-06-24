from __future__ import annotations
import arcade
import utils.paths as paths


class Coffre(arcade.Sprite):
    """Objet interactif boutique : ouvre un ShopMenu au contact du joueur."""

    INTERACTION_DISTANCE = 80

    def __init__(self, image: str, scale: float, name: str, catalogue: str,
                 x: float = 0.0, y: float = 0.0) -> None:
        super().__init__(image, scale)
        self.center_x  = x
        self.center_y  = y
        self.nom       = name
        self.catalogue = catalogue
