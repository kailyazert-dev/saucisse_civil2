import arcade
import replicate
import os
from dotenv import load_dotenv
from classes.humain import Humain, PNJ, Player
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, MOVEMENT_SPEED, PLAYER_SCALING
from assets.param_humain import IbmI_personnage

load_dotenv()
API_KEY = os.getenv("REPLICATE_API_TOKEN")

class BaseGameView(arcade.View):
    def __init__(self, environnement):
        super().__init__()
        # Pour les maps
        self.environnement = environnement
        self.tile_map = None
        self.scene = None
        self.physics_engine = None
        self.camera_sprites = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()
        self.camera_speed = 0.1
        # Pour les elements de la map
        self.player_sprite = None
        self.pnj_sprite = []
        self.current_pnj = None
        self.objet_sprites = []
        self.current_objet = None
        self.strategique_sprite = []
        self.current_strategique = None
        # Pour les dialogue
        self.current_input = ""
        self.last_response = ""
        self.is_typing = False

        # Ajout des gestionnaires séparés
        self.keycaps = Keycaps(self)
        self.interact = Interact(self)
        self.talk = Talk(self)

    """Permet de lier le manager à la vue."""
    def set_manager(self, manager):
        self.manager = manager

    """Creer les obstacle dans la carte"""
    def create_obstacles(self):
        return self.interact.create_obstacles()

    """Pour que la camera suit le player"""     
    def follow_player(self):
        position = (self.player_sprite.center_x, self.player_sprite.center_y)
        self.camera_sprites.position = arcade.math.lerp_2d(self.camera_sprites.position, position, self.camera_speed)

    """Pour avoir la position du player. rectangle enn bas de la carte"""
    def get_position(self):
        arcade.draw_rect_filled(arcade.rect.XYWH(self.width // 2, 20, self.width, 40), arcade.color.ALMOND)
        text = f"Scroll value: ({self.camera_sprites.position[0]:5.1f}, " \
               f"{self.camera_sprites.position[1]:5.1f})"
        arcade.draw_text(text, 10, 10, arcade.color.BLACK_BEAN, 20)






"""Class pour les touches de claviers"""
class Keycaps:
    def __init__(self, game_view):
        self.game_view = game_view

    def handle_key_press(self, key, modifiers):
        """Point d'entrée unique pour la gestion des touches pressées."""
        # 1. Réinitialisation si on bouge ou change de contexte
        self.to_reinit(key)

        # 2. Gestion du mouvement (retourne True si mouvement actif)
        if self.handle_movement_keys(key):
            return

        # 3. Gestion des dialogues avec PNJ
        self.to_dialogue(key)

        # 4. Gestion de l'upgrade de stats
        self.up_stat(key) 

    # Pour les touches de direction
    def handle_movement_keys(self, key):
        player = self.game_view.player_sprite
        if key == arcade.key.UP:
            player.change_y = MOVEMENT_SPEED
            player.direction = "up"
        elif key == arcade.key.DOWN:
            player.change_y = -MOVEMENT_SPEED
            player.direction = "down"
        elif key == arcade.key.LEFT:
            player.change_x = -MOVEMENT_SPEED
            player.direction = "left"
        elif key == arcade.key.RIGHT:
            player.change_x = MOVEMENT_SPEED
            player.direction = "right"
        elif key == arcade.key.P:
            print(player.humain.get_up())
        else:
            return False

        player.toggle_texture()
        return True

    def reset_movement_on_release(self, key, modifiers):
        player = self.game_view.player_sprite
        if key == arcade.key.UP:
            player.change_y = 0
            player.texture = player.textures["up"]
        elif key == arcade.key.DOWN:
            player.change_y = 0
            player.texture = player.textures["down"]
        elif key == arcade.key.LEFT:
            player.change_x = 0
            player.texture = player.textures["left"]
        elif key == arcade.key.RIGHT:
            player.change_x = 0
            player.texture = player.textures["right"]

    # Pour reinitialiser certains états si on bouge pendant une autre action
    def to_reinit(self, key):
        # Si on est en train de discuter et qu'on bouge → annuler
        if self.game_view.is_typing and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.game_view.is_typing = False
            self.game_view.last_response = ""
            self.game_view.current_input = ""
            self.game_view.current_pnj = None

        # Idem pour les stratégiques
        if self.game_view.current_strategique and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.game_view.current_strategique = None

        # Pour arreter l'augmentation des stats
        if self.game_view.current_objet and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.game_view.current_objet = None   
            self.game_view.player_sprite.stop_up()

    # Pour les dialogues
    def to_dialogue(self, key):
        player = self.game_view.player_sprite
        pnjs = self.game_view.pnj_sprite
        if key == arcade.key.LALT:
            for pnj in pnjs:
                if arcade.get_distance_between_sprites(player, pnj) < 50:
                    dx = player.center_x - pnj.center_x
                    dy = player.center_y - pnj.center_y
                    if abs(dx) > abs(dy):
                        pnj.texture = pnj.textures["right"] if dx > 0 else pnj.textures["left"]
                    else:
                        pnj.texture = pnj.textures["up"] if dy > 0 else pnj.textures["down"]
                    self.game_view.current_pnj = pnj
                    self.game_view.is_typing = True
                    self.game_view.current_input = ""
                    break

        elif self.game_view.is_typing and key == arcade.key.ENTER:
            if self.game_view.current_pnj:
                self.game_view.last_response = self.game_view.talk.talk_model(self.game_view.current_input, self.game_view.current_pnj)
            self.game_view.current_input = ""

        elif self.game_view.is_typing and key == arcade.key.BACKSPACE:
            self.game_view.current_input = self.game_view.current_input[:-1]    

    # Augmente une statistique si un objet progresseur et ENTER est pressé.
    def up_stat(self, key):
        if self.game_view.current_objet and key == arcade.key.ENTER:
            self.game_view.current_objet.utiliser(self.game_view.player_sprite)           





"""Classe pour les interactions"""
class Interact:
    def __init__(self, game_view):
        self.game_view = game_view

    def draw_interact_box(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        left = player.center_x + 25
        right = player.center_x + 200
        top = player.center_y - 25
        bottom = player.center_y - 75
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.WHITE)
        return left, top

    def create_obstacles(self):
        obstacles = arcade.SpriteList()
        obstacles.extend(self.game_view.pnj_sprite)
        obstacles.extend(self.game_view.strategique_sprite)
        obstacles.extend(self.game_view.objet_sprites)
        obstacles.extend(self.game_view.scene["Meuble_H"])
        obstacles.extend(self.game_view.scene["Mur"])
        return obstacles

    def interact_obj_prg(self):
        player = self.game_view.player_sprite
        for objet in self.game_view.objet_sprites:
            distance = arcade.get_distance_between_sprites(player, objet)
            if distance < 68:
                left, top = self.draw_interact_box()
                self.game_view.current_objet = objet
                stat_name = objet.stat_cible
                player_level_stat = getattr(player.humain, stat_name)
                if objet.stat_min < player_level_stat < objet.stat_max:
                    arcade.draw_text(objet.get_nom(), left + 15, top - 20, arcade.color.ORANGE, 14)
                    arcade.draw_text("ENTER : utiliser", left + 15, top - 40, arcade.color.LIGHT_GREEN, 14)
                else:
                    arcade.draw_text("Competence acquise", left + 15, top - 30, arcade.color.BLACK, 14)
                break

    def interact_pnj_strateg(self):
        player = self.game_view.player_sprite
        for strategique in self.game_view.strategique_sprite:
            distance = arcade.get_distance_between_sprites(player, strategique)
            if distance < 50:
                self.game_view.current_strategique = strategique
                arcade.draw_text("RALT : Aller à PHL", strategique.center_x - 90, strategique.center_y - 50, arcade.color.LIGHT_GREEN, 18)
                arcade.draw_text(strategique.get_nom(), strategique.center_x - 40, strategique.center_y + 40, arcade.color.ALLOY_ORANGE, 18)
                break

    def interact_pnj(self):
        player = self.game_view.player_sprite
        for pnj in self.game_view.pnj_sprite:
            distance = arcade.get_distance_between_sprites(player, pnj)
            if distance < 50:
                left, top = self.draw_interact_box()
                arcade.draw_text(pnj.get_nom(), left + 15, top - 20, arcade.color.ORANGE, 14)
                arcade.draw_text("LALT : Discuter", left + 15, top - 40, arcade.color.LIGHT_GREEN, 14)
        if self.game_view.is_typing and self.game_view.current_pnj:
            self.game_view.talk.draw_dialogue_box()





"""Class pour les discutions"""
class Talk:
    def __init__(self, game_view):
        self.game_view = game_view

    def draw_dialogue_box(self):
        arcade.get_window().use()
        if self.game_view.is_typing or self.game_view.last_response:
            margin = 15
            left = self.game_view.player_sprite.center_x - WINDOW_WIDTH // 2
            right = self.game_view.player_sprite.center_x + WINDOW_WIDTH // 2
            top = self.game_view.player_sprite.center_y - 100
            bottom = self.game_view.player_sprite.center_y - (WINDOW_HEIGHT // 2) - 10
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.WHITE)

        if self.game_view.is_typing:
            arcade.draw_text(
                f"{self.game_view.player_sprite.nom} : " + self.game_view.current_input,
                left + margin, top - margin - 15, arcade.color.BLACK, 14
            )

        if self.game_view.last_response:
            arcade.draw_text(
                f"{self.game_view.current_pnj.nom} : " + self.game_view.last_response,
                left + margin, top - margin - 40, arcade.color.LIGHT_GREEN, 14
            )

    def on_text(self, text):
        if self.game_view.is_typing:
            self.game_view.current_input += text

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
            system_prompt = "Tu es un personnage mystérieux. Reste vague et mystérieux."

        full_prompt = (
            f"{system_prompt}\n"
            f"Joueur: {message_joueur}\n"
            f"{pnj.nom}:"
        )
        try:
            output = replicate.run(
                "openai/gpt-4o-mini",
                input={
                    "prompt": full_prompt,
                    "max_new_tokens": 250,
                    "temperature": 0.7
                }
            )
            return "".join(output)
        except Exception as e:
            print("❌ Erreur lors de l'appel à replicate.run :", e)
            return "Désolé je suis occupé..."