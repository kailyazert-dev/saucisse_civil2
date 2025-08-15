import json
import arcade
from assets.param_map import MAP_WIDTH, MAP_HEIGHT, PLAYER_SCALING

class Humain:
    def __init__(self, charisme=0.1, rigidite=0.1, beauf=0.1, receptif_beauf=0.1, force=0.1, vitesse=0.1, endurance=0.1, mathematique=0.1, logique=0.1, rpg=0.1, music=0.1, langue=0.1, sociabilité=0.1, x=0, y=0):
        self.charisme = charisme
        self.rigidite = rigidite
        self.intensite_boof = beauf
        self.receptif_boof = receptif_beauf
        self.force = force
        self.vitesse = vitesse
        self.endurance = endurance
        self.mathematique = mathematique
        self.logique = logique
        self.rpg = rpg
        self.music = music
        self.langue = langue
        self.sociabilité = sociabilité
        self.x = x
        self.y = y    
    
    def get_stats_génétiques(self):
        return(
            f"charisme : {self.charisme}\n",
            f"rigidite : {self.rigidite}\n",
            f"intensite_boof : {self.intensite_boof}\n",
            f"receptif_boof : {self.receptif_boof}\n"
        )
    
    def get_stats_physique(self):
        return [
            ("Force", self.force),
            ("Vitesse", self.vitesse),
            ("Endurance", self.endurance),
        ]  
    def get_stats_intellect(self):
        return[
            ("Math", self.mathematique),
            ("Logique", self.logique),
            ("RPG", self.rpg),
        ]
    def get_stats_sociale(self):
        return[
            ("Musique", self.music),
            ("Langue", self.langue),
            ("Sociabilité", self.sociabilité),
        ]

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
    def __init__(self, humain, nom, image_file, quest_manager, character_manager, scale=PLAYER_SCALING):
        super().__init__(image_file, scale)
        self.humain = humain
        self.nom = nom
        self.quest_manager = quest_manager
        self.character_manager = character_manager

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

    def get_stat(self):
        print(
            f"Nom: {self.nom}\n"
            f"Force : {self.humain.force}\n"
        )

    def update(self, delta_time: float = 1/60):
        # pour update les stats
        self.character_manager.update_player_stats(delta_time)
        # pour les animations de déplacement
        self.character_manager.mouve.mouve(delta_time)    

      
