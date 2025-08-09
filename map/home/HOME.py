import arcade
import os
from classes.humain import Player
from classes.objet import Progresseur
from map.map_base import BaseGameView

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

        # Creer les objets
        livre = Progresseur("assets/images/bibliotheque.png", 1, "Multiplication", "mathematique", 0, 0.15)
        livre.center_x = 96
        livre.center_y = 910
        self.objet_sprites.append(livre)
        self.scene.add_sprite("Livre", livre)

        # Creer les obstacles
        obstacles = self.interact.create_obstacles()

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

        # Fonctions déclarées dans BaseGameView

        # Pour interagir avec les objets
        self.interact.interact_obj_prg()

        # Pour interagir avec les strategiques
        self.interact.interact_pnj_strateg()
            
        # Pour dialoguer avec les PNJ
        self.interact.interact_pnj()    

        # Pour aller à une autre map
        if 0 <= self.player_sprite.center_y <= 55 and 695 <= self.player_sprite.center_x <= 745 :
            left, top = self.interact.draw_interact_box()
            arcade.draw_text("RALT : PHL", left + 15, top - 30, arcade.color.LIGHT_GREEN, 14) 

        # Déssine la camera
        self.camera_gui.use()    

        # Pour avoir la position du joueur sur la carte
        self.get_position()      

    """Fonction pour ecrire le dialogue"""
    def on_text(self, text):
        if self.is_typing:
            self.talk.on_text(text)
            
    """ Fonction qui met à jour la map """
    def on_update(self, delta_time):
        self.physics_engine.update()  # physics_engine déclarer dans BaseGameView
        self.scene.update(delta_time) # scene déclarer dans BaseGameView
        self.follow_player()          # Fonction déclarer dans BaseGameView

    """ Fonction pour gérer les touches """
    def on_key_press(self, key, modifiers):

        # Apelle les fonctions de base
        self.keycaps.handle_key_press(key, modifiers) 

        # Pour aller à PHL
        if 0 <= self.player_sprite.center_y <= 55 and 695 <= self.player_sprite.center_x <= 745 and key == arcade.key.RALT:
            self.player_sprite.save_player()
            self.manager.switch_map("phl")
    
    def on_key_release(self, key, modifiers):
        self.keycaps.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
    

