import arcade
import os
from classes.humain import Player
from map.map_base import BaseGameView
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT

class GameView(BaseGameView):

    """ Configuration de la map """
    def setup(self, last_map):
        # Chemin vers la carte TMX
        home = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../home/HOME.tmx")

        # Charger la carte TMX
        self.tile_map = arcade.load_tilemap(home, scaling=1.0) # tile_map est dans BaseGameView

        # Créer la scène à partir de la tilemap
        self.scene = arcade.Scene.from_tilemap(self.tile_map) # scene est dans BaseGameView
        
        # Créer le joueur
        self.player_sprite =  Player.load_player(720, 50)     # create_player est dans BaseGameView
        self.scene.add_sprite("Player", self.player_sprite)   # ajoute le joueur à la liste des éléments de la scene

        # Creer les PNJs

        # Creer les strategiques

        # Creer les obstacles
        obstacles = self.create_obstacles()

        # Moteur physique sur les element de la map
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            obstacles
        )

    """ Fonction pour déssiner la map """
    def on_draw(self):
        self.clear()
        self.camera_sprites.use()
        self.scene.draw()

        # Pour interagir avec les strategiques
        for strategique in self.strategique_sprite:
            distance = arcade.get_distance_between_sprites(self.player_sprite, strategique)
            if distance < 50:
                self.current_strategique = strategique
                arcade.draw_text("RALT : Aller à la PHL", strategique.center_x - 90, strategique.center_y - 50, arcade.color.LIGHT_GREEN, 18) 
                arcade.draw_text(strategique.get_nom(), strategique.center_x - 40, strategique.center_y + 40, arcade.color.ALLOY_ORANGE, 18) 
                break
            
        # Pour dialoguer avec les PNJ
        for pnj in self.pnj_sprite:
            distance = arcade.get_distance_between_sprites(self.player_sprite, pnj)
            if distance < 50:
               arcade.draw_text("LALT : Discuter", pnj.center_x - 40, pnj.center_y - 40, arcade.color.LIGHT_GREEN, 18) 
               arcade.draw_text(pnj.get_nom(), pnj.center_x - 40, pnj.center_y + 40, arcade.color.ALLOY_ORANGE, 18) 

        # Déssine la camera
        self.camera_gui.use()    

        # Pour avoir la position du joueur sur la carte
        self.get_position()        # Fonction déclarer dans BaseGameView   

        if 0 <= self.player_sprite.center_y <= 55 and 695 <= self.player_sprite.center_x <= 745:
            arcade.draw_text("RALT : Armonie", WINDOW_WIDTH // 2 - 70 , WINDOW_HEIGHT // 2 - 60, arcade.color.LIGHT_GREEN, 18)    

    """ Fonction qui met à jour la map """
    def on_update(self, delta_time):
        self.physics_engine.update()  # physics_engine déclarer dans BaseGameView
        self.scene.update(delta_time) # scene déclarer dans BaseGameView
        self.follow_player()          # Fonction déclarer dans BaseGameView

    """ Fonction pour gérer les touches """
    def on_key_press(self, key, modifiers):
        # Si on est en train de discuter et qu'on bouge → annuler
        if self.is_typing and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.is_typing = False
            self.last_response = ""
            self.current_input = ""
            self.current_pnj = None

        # Idem pour les stratégiques
        if self.current_strategique and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.current_strategique = None

        # Déplacements généraux
        if self.handle_movement_keys(key):
            return

        # Dialogue PNJ
        if key == arcade.key.LALT:
            for pnj in self.pnj_sprite:
                if arcade.get_distance_between_sprites(self.player_sprite, pnj) < 50:
                    dx = self.player_sprite.center_x - pnj.center_x
                    dy = self.player_sprite.center_y - pnj.center_y
                    if abs(dx) > abs(dy):
                        pnj.texture = pnj.textures["right"] if dx > 0 else pnj.textures["left"]
                    else:
                        pnj.texture = pnj.textures["up"] if dy > 0 else pnj.textures["down"]
                    self.current_pnj = pnj
                    self.is_typing = True
                    self.current_input = ""
                    break

        elif self.is_typing and key == arcade.key.ENTER:
            if self.current_pnj:
                self.last_response = self.talk_model(self.current_input, self.api_key, self.current_pnj)
            self.current_input = ""

        elif self.is_typing and key == arcade.key.BACKSPACE:
            self.current_input = self.current_input[:-1]

        # Pour aller à PHL
        elif 0 <= self.player_sprite.center_y <= 55 and 695 <= self.player_sprite.center_x <= 745 and key == arcade.key.RALT:
            self.manager.switch_map("phl")
    
    def on_key_release(self, key, modifiers):
        self.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
    

