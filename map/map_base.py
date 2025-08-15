import arcade
import replicate
import os
from dotenv import load_dotenv
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, MOVEMENT_SPEED, PLAYER_SCALING
from assets.param_humain import IbmI_personnage

load_dotenv()
API_KEY = os.getenv("REPLICATE_API_TOKEN")

class BaseGameView(arcade.View):
    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__()
        # Pour les maps
        self.environnement = environnement
        self.tile_map = None
        self.scene = None
        self.physics_engine = None
        self.camera_sprites = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()
        self.camera_speed = 0.1
        # Pour les characteres
        self.character_manager = character_manager
        self.player_sprite = None
        self.pnj_sprite = []
        self.current_pnj = None
        # pour les objets
        self.objet_sprites = []
        self.current_objet = None
        self.strategique_sprite = []
        self.current_strategique = None
        # Pour les dialogue
        self.current_input = ""
        self.last_response = ""
        self.is_typing = False
        # Pour les stat_box
        self.quest_manager = quest_manager
        self.show_stats = False
        self.show_quests = False

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

    def on_mouse_press(self, x, y, button, modifiers):

        # --- 1️⃣ Détection dans le monde principal ---
        world_pos = self.game_view.camera_sprites.unproject((x, y))
        world_x, world_y = world_pos.x, world_pos.y

        # for element in self.game_view.objet_sprites:
        #     if element.left <= world_x <= element.right and element.bottom <= world_y <= element.top:
        #         print(f"💡 Tu as cliqué sur {element.get_nom()}")
        #         self.game_view.current_objet = element
        #         return  # on arrête ici si trouvé

        # --- 2️⃣ Détection dans la box des stats ---
        if self.game_view.show_stats:
            # Conversion du clic avec la caméra mini-map
            mini_world_pos = self.game_view.interact.mini_map_camera.unproject((x, y))
            mini_x, mini_y = mini_world_pos.x, mini_world_pos.y

            for tile in self.game_view.interact.choise_stat:
                if tile.left <= mini_x <= tile.right and tile.bottom <= mini_y <= tile.top:
                    self.game_view.interact.sous_box = self.game_view.interact.stat_map.sprite_lists["Stats-base"]
                    return
            for tile in self.game_view.interact.choise_bag:
                if tile.left <= mini_x <= tile.right and tile.bottom <= mini_y <= tile.top:
                    self.game_view.interact.sous_box = self.game_view.interact.stat_map.sprite_lists["Bag-base"]
                    return

    def handle_key_press(self, key, modifiers):
        """Point d'entrée unique pour la gestion des touches pressées."""
        # 1. Réinitialisation si on bouge ou change de contexte
        self.to_reinit(key)

        # 2. Gestion du mouvement (retourne True si mouvement actif)
        if self.handle_movement_keys(key):
            return

        # 3. Gestion des paneaux
        self.to_show_stat(key)
        self.to_show_quests(key)

        # 4. Gestion des dialogues avec PNJ
        self.to_dialogue(key)

        # 5. Gestion de l'upgrade de stats
        self.up_stat(key) 

    # Pour les touches de direction
    def handle_movement_keys(self, key):
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = MOVEMENT_SPEED
            player.direction = "up"
        elif key == arcade.key.S:
            player.change_y = -MOVEMENT_SPEED
            player.direction = "down"
        elif key == arcade.key.Q:
            player.change_x = -MOVEMENT_SPEED
            player.direction = "left"
        elif key == arcade.key.D:
            player.change_x = MOVEMENT_SPEED
            player.direction = "right"
        else:
            return False            
        player.toggle_texture()
        return True

    def reset_movement_on_release(self, key, modifiers):
        player = self.game_view.player_sprite
        if key == arcade.key.Z:
            player.change_y = 0
            player.texture = player.textures["up"]
        elif key == arcade.key.S:
            player.change_y = 0
            player.texture = player.textures["down"]
        elif key == arcade.key.Q:
            player.change_x = 0
            player.texture = player.textures["left"]
        elif key == arcade.key.D:
            player.change_x = 0
            player.texture = player.textures["right"]

    # Pour reinitialiser certains états si on bouge pendant une autre action
    def to_reinit(self, key):
        # Si on est en train de discuter et qu'on bouge → annuler
        if self.game_view.is_typing and key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D):
            self.game_view.is_typing = False
            self.game_view.last_response = ""
            self.game_view.current_input = ""
            self.game_view.current_pnj = None

        # Idem pour les stratégiques
        if self.game_view.current_strategique and key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D):
            self.game_view.current_strategique = None

        # Pour arreter l'augmentation des stats
        if self.game_view.current_objet and key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D):
            self.game_view.current_objet = None   
            # self.character_manager.stop_up()

    # Augmente une statistique si un objet progresseur et ENTER est pressé.
    def up_stat(self, key):
        if self.game_view.current_objet and key == arcade.key.ENTER:
            self.game_view.current_objet.utiliser(self.game_view.player_sprite, self.game_view.character_manager)   

    # Pour les paneaux
    def to_show_stat(self, key):
        if key == arcade.key.P:
            self.game_view.show_stats = not self.game_view.show_stats  
    def to_show_quests(self, key):
        if key == arcade.key.O:
            self.game_view.show_quests = not self.game_view.show_quests
            quest_act = next((q for q in self.game_view.quest_manager.arc.quests if q.status == "ec"), None)
            print(quest_act.title, quest_act.description, quest_act.status)
            for obj in quest_act.objectives:
                print(obj.name, obj.description, obj.status)
                  

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

            





"""Classe pour les interactions"""
class Interact:
    def __init__(self, game_view):
        self.game_view = game_view
        # chemin vers les fichier TMX
        box_stats_tmx_path = "map/map_tmx/stat_box.tmx"
        box_quests_tmx_path = "map/map_tmx/quests_box.tmx"

        # fichier TMX
        self.stat_map = arcade.load_tilemap(box_stats_tmx_path, scaling=1)
        self.quest_map = arcade.load_tilemap(box_quests_tmx_path, scaling=1)

        # les claques de box_stat
        self.box_stat = arcade.Scene.from_tilemap(self.stat_map)
        self.base = self.stat_map.sprite_lists["Base"]
        self.top = self.stat_map.sprite_lists["Top-base"]
        self.choise_stat = self.stat_map.sprite_lists["Choise_1"]
        self.choise_bag = self.stat_map.sprite_lists["Choise_2"]
        self.sous_box = self.stat_map.sprite_lists["Stats-base"]
        self.box_quest = arcade.Scene.from_tilemap(self.quest_map)

        self.mini_map_camera = arcade.Camera2D()

    # Déssine la stat_box
    def draw_box(self):
        if self.game_view.show_stats:
            
            # Activer la caméra mini-map
            self.mini_map_camera.use()
            # Positionner la caméra
            self.mini_map_camera.position = (WINDOW_WIDTH//2 - 180, WINDOW_HEIGHT//2)

            # Dessiner la box des stats + ecri les stats
            # self.box_stat.draw()
            self.base.draw()
            self.top.draw()
            self.choise_stat.draw()
            self.choise_bag.draw()
            self.sous_box.draw()
            arcade.draw_text("Physique ", 230, 640, arcade.color.ORANGE, 18)
            arcade.draw_text("Intellect ", 230, 592, arcade.color.ORANGE, 18)
            arcade.draw_text("Sociale ", 230, 544, arcade.color.ORANGE, 18)
            if self.sous_box == self.stat_map.sprite_lists["Stats-base"]:
                y = 325
                arcade.draw_text("Stats physique :", 105, 350, arcade.color.ORANGE, 18)
                for key, value in self.game_view.player_sprite.humain.get_stats_physique():
                    arcade.draw_text(f"{key} : {value}", 105, y, arcade.color.BLACK, 18)
                    y -= 25    
                arcade.draw_text("Stats intellectuel :", 305, 350, arcade.color.ORANGE, 18)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_intellect():
                    arcade.draw_text(f"{key} : {value}", 305, y, arcade.color.BLACK, 18)
                    y -= 25    
                arcade.draw_text("Stats sociale :", 505, 350, arcade.color.ORANGE, 18)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_sociale():
                    arcade.draw_text(f"{key} : {value}", 505, y, arcade.color.BLACK, 18)
                    y -= 25    

            # Réactiver la caméra principale (celle qui suit le joueur)
            self.game_view.camera_sprites.use()
        
        if self.game_view.show_quests:
            # Activer la caméra mini-map
            self.mini_map_camera.use()
            # Positionner la caméra
            self.mini_map_camera.position = (WINDOW_WIDTH//2 - 180, WINDOW_HEIGHT//2)
            
            # Dessiner la box des quests + ecri les quêtes
            self.box_quest.draw()

            # Réactiver la caméra principale (celle qui suit le joueur)
            self.game_view.camera_sprites.use()
            

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

    # Pour les object progresseur
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