import json
import arcade
from assets.param_map import MAP_WIDTH, MAP_HEIGHT, PLAYER_SCALING
from quests.quest_manager import QuestManager

class Humain:
    def __init__(self, charisme=0.1, rigidite=0.1, beauf=0.1, receptif_beauf=0.1, force=0.1, vitesse=0.1, endurance=0.1, mathematique=0.1, logique=0.1, rpg=0.1, music=0.1, langue=0.1, sociale=0.1, x=0, y=0):
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
        self.sociale = sociale
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
        return(
            f"Force : {self.force}\n"
            f"vitesse : {self.vitesse}\n"
            f"endurance : {self.endurance}\n"
        )   
    def get_stats_intelecte(self):
        return(
            f"mathematique : {self.mathematique}\n"
            f"logique : {self.logique}\n"
            f"rpg : {self.rpg}"
        )   
    def get_stats_sociale(self):
        return(
            f"music : {self.music}\n"
            f"langue : {self.langue}\n"
            f"sociale : {self.sociale}\n"
        )   

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
    def __init__(self, humain, nom, image_file, quest_manager, scale=PLAYER_SCALING):
        super().__init__(image_file, scale)
        self.humain = humain
        self.nom = nom
        self.quest_manager = quest_manager

        # Pour les augmentations
        self.up = False
        self.time_since_last_up_increase = 0.0
        self.up_increase_interval = 2.0
        self.stat_to_up = None

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

    def start_up(self, stat_cible, objet_progresseur=None):
        """Démarre l’augmentation progressive des stats."""
        self.up = True
        self.stat_to_up = stat_cible
        self.time_since_last_up_increase = 0.0
        self.current_progresseur = objet_progresseur

    def stop_up(self):
        """Arrête l’augmentation des stats."""
        self.up = False

    def update(self, delta_time: float = 1/60):
        """ Augmentation des stats """
        if self.up:
            self.time_since_last_up_increase += delta_time
            if self.time_since_last_up_increase >= self.up_increase_interval:
                if self.stat_to_up:
                    current_value = getattr(self.humain, self.stat_to_up, None)
                    if current_value is not None:
                        new_value = round(current_value + 0.002, 3)
                        stat = self.stat_to_up
                        self.quest_manager.check_objective(stat, new_value)
                        if self.current_progresseur:
                            max_value = self.current_progresseur.stat_max
                            if new_value > max_value:
                                print(f"🚫 {self.stat_to_up} a atteint la limite ({max_value:.3f})")
                                self.stop_up()
                                return

                        setattr(self.humain, self.stat_to_up, new_value)
                        print(f"{self.nom} a gagné +0.002 en {self.stat_to_up} → {new_value:.3f}")
                        self.save_player()
                    else:
                        print(f"⚠️ La stat '{self.stat_to_up}' n'existe pas.")
                self.time_since_last_up_increase = 0.0

        """ Move the player """
        # Move player.
        # Remove these lines if physics engine is moving player.
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Appelle l’update parent
        super().update(delta_time)

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

    """ Pour sauvegarder les stats du player. """
    def save_player(self):
        stats = {
            "nom": self.nom,
            "charisme": self.humain.charisme,
            "rigidite": self.humain.rigidite,
            "intensite_boof": self.humain.intensite_boof,
            "receptif_boof": self.humain.receptif_boof,
            "force": self.humain.force,
            "vitesse": self.humain.vitesse,
            "endurance": self.humain.endurance,
            "mathematique": self.humain.mathematique,
            "logique": self.humain.logique,
            "music": self.humain.music,
            "langue": self.humain.langue,
            "sociale": self.humain.sociale,
            "x": self.humain.x,
            "y": self.humain.y,
        }
        filename = 'save/stats.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
            
    """ Pour charger le player. """
    @staticmethod
    def load_player(x, y, quest_manger, scale=PLAYER_SCALING):
        filename = 'save/stats.json'
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        humain = Humain(
            charisme=data["charisme"],
            rigidite=data["rigidite"],
            beauf=data["intensite_boof"],
            receptif_beauf=data["receptif_boof"],
            force=data["force"],
            vitesse=data["vitesse"],
            endurance=data["endurance"],
            mathematique=data["mathematique"],
            logique=data["logique"],
            music=data["music"],
            langue=data["langue"],
            sociale=data["sociale"],
            x = x,                                                         
            y = y
        )
        image_file = 'assets/images/player_d.png'
        player = Player(humain, data["nom"], image_file, quest_manger, scale)
        player.center_x = x
        player.center_y = y
        return player        
