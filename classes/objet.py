import arcade

class Objet(arcade.Sprite):
    def __init__(self, image_path, scale):
        super().__init__(image_path, scale)