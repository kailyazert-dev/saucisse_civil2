import arcade
import replicate
import os
from dotenv import load_dotenv
from openai import OpenAI
from classes.humain import Humain, PNJ, Player
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, MOVEMENT_SPEED, PLAYER_SCALING
from assets.param_humain import IbmI_personnage

load_dotenv()
API_KEY = os.getenv("REPLICATE_API_TOKEN")

class BaseGameView(arcade.View):
    def __init__(self, environnement):
        super().__init__()

        # Pour l'environement
        self.environnement = environnement

        # Pour la map
        self.tile_map = None
        self.scene = None
        self.physics_engine = None
        self.camera_sprites = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()
        self.camera_speed = 0.1

        # Pour le jouer
        self.player_sprite = None

        # Pour les PNJ
        self.pnj_sprite = []
        self.current_pnj = None           # Pour le PNJ en face

        # Pour les objets
        self.objet_sprites = []
        self.current_objet = None

        # Pour les strategiques
        self.strategique_sprite = []
        self.current_strategique = None   # Pour le strategique en face

        # Pour le model et les discution
        self.current_input = ""           # Le message du player
        self.last_response = ""           # La reponse du model
        self.is_typing = False            # Ouverture du champ du dialogue 

    def set_manager(self, manager):
        self.manager = manager
    
    """Pour creer les obstacles de la map"""
    def create_obstacles(self):
        obstacles = arcade.SpriteList()                    # Creer la liste des obstacles
        obstacles.extend(self.pnj_sprite)                  # Ajoute la liste des pnj
        obstacles.extend(self.strategique_sprite)          # Ajoute la liste des strategique
        obstacles.extend(self.objet_sprites)               # Ajoute la liste des objets
        obstacles.extend(self.scene["Meuble_H"])           # Ajoute les meubles de la map
        obstacles.extend(self.scene["Mur"])                # Ajoute les murs de la map
        return obstacles
    
    """Pour dessiner la boite de dialogues"""
    def draw_dialogue_box(self):
        arcade.get_window().use()
        if self.is_typing or self.last_response:
            margin = 15
            left = self.player_sprite.center_x - WINDOW_WIDTH // 2
            right = self.player_sprite.center_x + WINDOW_WIDTH // 2
            top = self.player_sprite.center_y - 100
            bottom = self.player_sprite.center_y - (WINDOW_HEIGHT // 2) - 10
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.WHITE)

        if self.is_typing:
            arcade.draw_text(
                f"{self.player_sprite.nom} : " + self.current_input,
                left + margin, top - margin - 15, arcade.color.BLACK, 14
            )
        if self.last_response:
            arcade.draw_text(
                f"{self.current_pnj.nom} : " + self.last_response,
                left + margin, top - margin - 40, arcade.color.LIGHT_GREEN, 14
            )

    """Pour les touches de fonctions"""
    def handle_movement_keys(self, key):
        if key == arcade.key.UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
            self.player_sprite.direction = "up"
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
            self.player_sprite.direction = "down"
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
            self.player_sprite.direction = "left"
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED
            self.player_sprite.direction = "right"
        elif key == arcade.key.P:
            print(self.player_sprite.humain.get_up())     
        else:
            return False
        
        self.player_sprite.toggle_texture()
        return True
    
    """Pour les animations du player lorsqu'il marche"""
    def reset_movement_on_release(self, key, modifiers):
        if key == arcade.key.UP:
            self.player_sprite.change_y = 0
            self.player_sprite.texture = self.player_sprite.textures["up"]
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = 0
            self.player_sprite.texture = self.player_sprite.textures["down"]
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = 0
            self.player_sprite.texture = self.player_sprite.textures["left"]
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
            self.player_sprite.texture = self.player_sprite.textures["right"]

    """Pour que la camera suit le joueur"""
    def follow_player(self):
        position = (self.player_sprite.center_x, self.player_sprite.center_y)
        self.camera_sprites.position = arcade.math.lerp_2d(self.camera_sprites.position, position, self.camera_speed)        
    
    """Pour écrire du texte pour la discution """
    def on_text(self, text):
        if self.is_typing:
            self.current_input += text

    """Pour parler entre PNJ"""
    def talk_model(self, message_joueur, pnj):
        
        os.environ["REPLICATE_API_TOKEN"] = API_KEY

        nom_pnj = pnj.nom
        if nom_pnj in IbmI_personnage.personnages:
            data = IbmI_personnage.personnages[nom_pnj]
            system_prompt = (
                    f"Tu est {data['nom']}, un personnage {data['type']}.\n"
                    f"Ton metier est {data['metier']}.\n"
                    f"Tu a une personalité {data['personnalite']}.\n"
                    f"Tes hobbies sont {data['hobbie']}.\n"
                    f"Repond court, sans émoji."
                )
        else:
            system_prompt = "Tu es un personnage mystérieux. Reste vague et mystérieux. Ne révèle jamais ton personnage."   

        full_prompt = (
            f"{system_prompt}\n"
            f"Joueur: {message_joueur}\n"
            f"{pnj.nom}:"
        )
        try:
            output = replicate.run(
                "openai/gpt-4o-mini",
                # "ibm-granite/granite-3.3-8b-instruct",
                input={
                    "prompt": full_prompt,
                    "max_new_tokens": 250,
                    "temperature": 0.7
                }
            )
            print("Réponse du model générée :\n")
            print("".join(output))
            return "".join(output)
        except Exception as e:
            print("❌ Erreur lors de l'appel à replicate.run :")
            print(e)
            return "Desoler je suis occupé..."
        
    """Pour avoir la position du joueur sur la carte""" 
    def get_position(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(self.width // 2, 20, self.width, 40),
                                arcade.color.ALMOND)
        text = f"Scroll value: ({self.camera_sprites.position[0]:5.1f}, " \
               f"{self.camera_sprites.position[1]:5.1f})"
        arcade.draw_text(text, 10, 10, arcade.color.BLACK_BEAN, 20)   

