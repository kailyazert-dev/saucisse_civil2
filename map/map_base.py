import arcade
import replicate
import os
from dotenv import load_dotenv
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, MOVEMENT_SPEED, KENNY
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
        self.current_collection = None
        self.open_collection = False
        self.current_index_upstat = 0
        self.current_select_upstat = 0
        self.strategique_sprite = []
        self.current_strategique = None
        # Pour les dialogue
        self.current_input = ""
        self.last_response = ""
        self.is_typing = False
        # Pour les quest/quest_box
        self.quest_manager = quest_manager
        self.show_quests = False
        self.quest_texture = arcade.load_texture("map/map_tmx/bottom1.png")
        self.quest_width = self.quest_texture.width * 0.5
        self.quest_height = self.quest_texture.height * 0.5
        self.quest_x = 30 + self.quest_width / 2
        self.quest_y = WINDOW_HEIGHT - 30 - self.quest_height / 2
        self.show_side_bar = False

        # Pour les stats
        self.show_stats = False

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

    """Pour afficher la side-bar"""
    def get_quests(self):
        if not self.show_stats and not self.show_quests:
            arcade.draw_texture_rect(self.quest_texture, arcade.XYWH(30, WINDOW_HEIGHT-28, self.quest_texture.width, self.quest_texture.height).scale(0.5))
            arcade.draw_text("Quests:", 50, self.height - 40, arcade.color.WHITE, 14, bold=True, font_name=KENNY)

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

        left = self.game_view.quest_x - self.game_view.quest_width 
        right = self.game_view.quest_x + self.game_view.quest_width 
        bottom = self.game_view.quest_y - self.game_view.quest_height / 2
        top = self.game_view.quest_y + self.game_view.quest_height 

        if left <= x <= right and bottom <= y <= top:
            self.game_view.show_side_bar = not self.game_view.show_side_bar

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
        self.game_view.character_manager.animation.update()
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
            self.game_view.character_manager.stop_up()
            self.game_view.character_manager.player.reading = False
        if self.game_view.current_collection and key in (arcade.key.Z, arcade.key.S, arcade.key.Q, arcade.key.D):
            self.game_view.current_collection = None   
            self.game_view.open_collection = False   
            self.game_view.character_manager.stop_up()
            self.game_view.character_manager.player.reading = False

    # Augmente une statistique si un objet progresseur et ENTER est pressé.
    def up_stat(self, key):
        if self.game_view.current_objet and key == arcade.key.ENTER:
            self.game_view.current_objet.utiliser(self.game_view.player_sprite, self.game_view.character_manager) 

        elif self.game_view.current_collection:
            if key == arcade.key.ENTER:
                if self.game_view.open_collection:
                    livre_selectionne = self.game_view.current_collection.upStats[self.game_view.current_index_upstat]
                    self.game_view.character_manager.player.reading = True
                    livre_selectionne.utiliser(self.game_view.player_sprite, self.game_view.character_manager) 
                else:
                    self.game_view.open_collection = True

            elif self.game_view.open_collection:
                if key == arcade.key.UP:
                    self.game_view.current_index_upstat -= 1
                    if self.game_view.current_index_upstat < 0:
                        self.game_view.current_index_upstat = len(self.game_view.current_collection.upStats) - 1
                elif key == arcade.key.DOWN:
                    self.game_view.current_index_upstat += 1
                    if self.game_view.current_index_upstat >= len(self.game_view.current_collection.upStats):
                        self.game_view.current_index_upstat = 0 
                


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

    # Affiche les quêtes à gauche de l'ecrran
    def draw_side_bar(self):
        if not self.game_view.show_stats and not self.game_view.show_quests and self.game_view.show_side_bar:
            y = WINDOW_HEIGHT - 67
            quest = next((q for q in self.game_view.quest_manager.arc.quests if q.status == "ec"), None)
            arcade.draw_text(f"{quest.title}", 20, y, arcade.color.WHITE, 14, bold=True, font_name=KENNY)
            y -= 20
            for obj in quest.objectives:
                color = arcade.color.JADE if obj.status=="t" else arcade.color.WHITE
                arcade.draw_text(f"{obj.name}", 30, y, color, 12, bold=True, font_name=KENNY)
                y -= 20
               

    # Déssine la stat_box
    def draw_box(self):     

        # Dessiner la box des stats + ecri les stats
        if self.game_view.show_stats:
            self.base.draw()
            self.top.draw()
            self.choise_stat.draw()
            self.choise_bag.draw()
            self.sous_box.draw()
            arcade.draw_text("Physique", 360, 640, arcade.color.ORANGE, 12, font_name=KENNY)
            arcade.draw_text("Intellect", 360, 592, arcade.color.ORANGE, 12, font_name=KENNY)
            arcade.draw_text("Sociale", 360, 544, arcade.color.ORANGE, 12, font_name=KENNY)
            if self.sous_box == self.stat_map.sprite_lists["Stats-base"]:
                y = 325
                arcade.draw_text("Stats physique", 247, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                for key, value in self.game_view.player_sprite.humain.get_stats_physique():
                    arcade.draw_text(f"{key} : {value}", 247, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25    
                arcade.draw_text("Stats intellect", 447, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_intellect():
                    arcade.draw_text(f"{key} : {value}", 447, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25 
                arcade.draw_text("Stats sociale", 647, 350, arcade.color.ORANGE, 12, font_name=KENNY)
                y = 325
                for key, value in self.game_view.player_sprite.humain.get_stats_sociale():
                    arcade.draw_text(f"{key} : {value}", 647, y, arcade.color.BLACK, 12, font_name=KENNY)
                    y -= 25   
            # desac_cam()         
        
        # Dessiner la box des quêtes
        if self.game_view.show_quests:
            self.box_quest.draw()  

    def create_obstacles(self):
        obstacles = arcade.SpriteList()
        obstacles.extend(self.game_view.pnj_sprite)
        obstacles.extend(self.game_view.strategique_sprite)
        obstacles.extend(self.game_view.objet_sprites)
        obstacles.extend(self.game_view.scene["Meuble_H"])
        obstacles.extend(self.game_view.scene["Mur"])
        return obstacles

    def get_r_corner_cord(self):
        arcade.get_window().use()
        player = self.game_view.player_sprite
        left = player.center_x + 20
        top = player.center_y - 55
        return left, top
    
    # Pour les objects progresseur
    def interact_obj_prg(self):
        self.box_text = arcade.load_texture("map/map_tmx/use_box.png")
        self.box_text_t = arcade.load_texture("map/map_tmx/use_box_t.png")
        self.box_text_c = arcade.load_texture("map/map_tmx/use_box_c.png")
        self.box_text_b = arcade.load_texture("map/map_tmx/use_box_b.png")
        box_width = self.box_text.width - 10
        box_height = self.box_text.height - 40
        player = self.game_view.player_sprite

        for objet in self.game_view.objet_sprites:
            distance = arcade.get_distance_between_sprites(player, objet)
            if distance < 68:
                left, top = self.get_r_corner_cord()
                # Si c'est un upstat
                if type(objet).__name__ == "UpStat":
                    self.game_view.current_objet = objet
                    stat_name = objet.stat_cible
                    player_level_stat = getattr(player.humain, stat_name)
                    arcade.draw_texture_rect(self.box_text, arcade.XYWH(left + box_width /2, top, box_width, box_height))
                    color = (
                        arcade.color.GRAY_BLUE if player_level_stat >= objet.stat_max
                        else arcade.color.RED if player_level_stat < objet.stat_min
                        else arcade.color.JADE
                    )
                    arcade.draw_text(f"{objet.get_name()}", left, top-7, color, 12, box_width, "center", font_name=KENNY)

                # si c'est une collection d'upstat
                if type(objet).__name__ == "UpStatCollection": 
                    self.game_view.current_collection = objet
                    box_width += 10
                    arcade.draw_texture_rect(self.box_text, arcade.XYWH(left + box_width /2, top, box_width, box_height))
                    arcade.draw_text(f"{objet.get_name()}", left, top-7, arcade.color.JADE, 12, box_width, "center", font_name=KENNY)
                    # Si le joueur appuie sur ENTER
                    if self.game_view.current_collection and self.game_view.open_collection:
                        upstats = objet.get_all_upStats()
                        box_t_height = self.box_text_t.height - 8
                        box_c_height = self.box_text_c.height - 13
                        y_cursor = top - box_height / 2 - 4
                        arcade.draw_texture_rect(self.box_text_t, arcade.XYWH(left + box_width /2, y_cursor, box_width, box_t_height))
                        y_cursor -= box_c_height / 2 + 3
                        y_pos = y_cursor + box_t_height / 2 - 4
                        for i, upstat in enumerate(upstats):
                            stat_name = upstat.stat_cible  
                            color = (
                                arcade.color.GRAY_BLUE if player_level_stat >= upstat.stat_max
                                else arcade.color.RED if player_level_stat < upstat.stat_min
                                else arcade.color.JADE
                            )                                                                     
                            player_level_stat = getattr(player.humain, stat_name)                                     
                            arcade.draw_texture_rect(self.box_text_c, arcade.XYWH(left + box_width /2, y_cursor, box_width, box_c_height))
                            prefix = "→ " if i == self.game_view.current_index_upstat else "  "        
                            arcade.draw_text(f"{prefix}", left+7, y_pos, arcade.color.BLACK, 10)
                            arcade.draw_text(f"{upstat.get_name()}", left+26, y_pos, color, 10, font_name=KENNY)
                            y_cursor -= box_c_height
                            y_pos -= 35
                        y_cursor += box_c_height / 2   
                        arcade.draw_texture_rect(self.box_text_b, arcade.XYWH(left + box_width /2 , y_cursor, box_width, box_t_height))    
                    break

    def interact_pnj_strateg(self):
        player = self.game_view.player_sprite
        for strategique in self.game_view.strategique_sprite:
            distance = arcade.get_distance_between_sprites(player, strategique)
            if distance < 50:
                self.game_view.current_strategique = strategique
                arcade.draw_text("RALT : Aller à PHL", strategique.center_x - 90, strategique.center_y - 50, arcade.color.LIGHT_GREEN, 14, font_name=KENNY)
                arcade.draw_text(strategique.get_nom(), strategique.center_x - 40, strategique.center_y + 40, arcade.color.ALLOY_ORANGE, 14, font_name=KENNY)
                break

    def interact_pnj(self):
        player = self.game_view.player_sprite
        for pnj in self.game_view.pnj_sprite:
            distance = arcade.get_distance_between_sprites(player, pnj)
            if distance < 50:
                left, top = self.draw_interact_box()
                arcade.draw_text(pnj.get_nom(), left + 15, top - 20, arcade.color.ORANGE, 14, font_name=KENNY)
                arcade.draw_text("LALT : Discuter", left + 15, top - 40, arcade.color.LIGHT_GREEN, 14, font_name=KENNY)
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