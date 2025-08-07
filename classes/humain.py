import random
import arcade
from assets.param_map import MAP_WIDTH, MAP_HEIGHT, PLAYER_SCALING

class Humain:
    def __init__(self, charisme, rigidite, intensite_boof, receptif_boof, x=0, y=0):
        self.charisme = charisme
        self.rigidite = rigidite
        self.intensite_boof = intensite_boof
        self.receptif_boof = receptif_boof
        self.x = x
        self.y = y

    def get_stat(self):
        return(
            f"Intensité de boofitude : {self.intensite_boof}\n"
            f"Réceptivité à la boofitude : {self.receptif_boof}\n"
            f"Charisme : {self.charisme}"
        )
    
    def get_intensite_boof(self):
        return(self.intensite_boof)

class PNJ(arcade.Sprite):
    def __init__(self, nom, humain, type, image_path, scale):
        super().__init__(image_path, scale)
        self.nom = nom
        self.humain = humain
        self.type = type
        self.center_x = humain.x
        self.center_y = humain.y
        self.image_path = image_path
        self.textures = {
            "up": arcade.load_texture("assets/images/player_u.png"),
            "down": arcade.load_texture("assets/images/player_d.png"),
            "left": arcade.load_texture("assets/images/player_l.png"),
            "right": arcade.load_texture("assets/images/player_r.png"),
        }

    def get_nom(self):
        return(f"{self.nom}")    

class Player(arcade.Sprite):
    def __init__(self, humain, nom, image_file, scale=PLAYER_SCALING):
        super().__init__(image_file, scale)
        self.nom = nom
        self.textures = {
            "up": arcade.load_texture("assets/images/player_u.png"),
            "down": arcade.load_texture("assets/images/player_d.png"),
            "left": arcade.load_texture("assets/images/player_l.png"),
            "right": arcade.load_texture("assets/images/player_r.png"),
        }
        self.textures_up = [
            arcade.load_texture("assets/images/player_u1.png"),
            arcade.load_texture("assets/images/player_u2.png")
        ]
        self.textures_down = [
            arcade.load_texture("assets/images/player_d1.png"),
            arcade.load_texture("assets/images/player_d2.png")
        ]
        self.textures_left = [
            arcade.load_texture("assets/images/player_l1.png"),
            arcade.load_texture("assets/images/player_l2.png")
        ]
        self.textures_right = [
            arcade.load_texture("assets/images/player_r1.png"),
            arcade.load_texture("assets/images/player_r2.png")
        ]
        self.current_texture_index = 0                 
        self.time_since_last_texture_change = 0.0      # timer initiale
        self.texture_switch_interval = 0.2             # timer pour changer de pas lors de la marche
        self.direction = "down"                        # direction de base du player

    def update(self, delta_time: float = 1/60):
        """ Move the player """
        # Move player.
        # Remove these lines if physics engine is moving player.
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Check for out-of-bounds
        if self.left < 0:
            self.left = 0
        elif self.right > MAP_WIDTH - 1:
            self.right = MAP_WIDTH - 1

        if self.bottom < 0:
            self.bottom = 0
        elif self.top > MAP_HEIGHT - 1:
            self.top = MAP_HEIGHT - 1

        # Animation : alterne la texture toutes les 0.2s si le joueur bouge
        if self.change_x != 0 or self.change_y != 0:
            self.time_since_last_texture_change += delta_time
            if self.time_since_last_texture_change >= self.texture_switch_interval:
                self.toggle_texture()
                self.time_since_last_texture_change = 0.0
        else:
            # Si le joueur ne bouge pas, remettre la texture fixe correspondant à la direction
            if self.direction == "up":
                self.texture = self.textures["up"]
            elif self.direction == "down":
                self.texture = self.textures["down"]
            elif self.direction == "left":
                self.texture = self.textures["left"]
            elif self.direction == "right":
                self.texture = self.textures["right"]    

    def toggle_texture(self):
        self.current_texture_index = 1 - self.current_texture_index  # Alterne 0 <-> 1

        if self.direction == "up":
            self.texture = self.textures_up[self.current_texture_index]
        elif self.direction == "down":
            self.texture = self.textures_down[self.current_texture_index]
        elif self.direction == "left":
            self.texture = self.textures_left[self.current_texture_index]
        elif self.direction == "right":
            self.texture = self.textures_right[self.current_texture_index]        