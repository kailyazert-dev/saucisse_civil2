import arcade
import json
import os
from character.character_classes import Humain, PNJ, Player
from assets.param_map import PLAYER_SCALING
from map.map_base import BaseGameView
from map.map_classes.objet import UpStat

class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager):
        super().__init__(environnement, quest_manager)
        self.quest_manager = quest_manager

    """ Configuration de la map """
    def setup(self, last_map):
        # Chemin vers la carte TMX
        home = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../armonie/PHL.tmx")

        # Charger la carte TMX
        self.tile_map = arcade.load_tilemap(home, scaling=1.0) # tile_map est dans BaseGameView

        # Créer la scène à partir de la tilemap
        self.scene = arcade.Scene.from_tilemap(self.tile_map) # scene est dans BaseGameView
        
        # Point d'entrer de la map
        entry_positions = {
            "tma": (2792, 1848),    # Si le joueur vient de la map tma
            "home": (574, 50),      # Si le joueur vient de la map home
        }
        default_position = (72, 72)  # Position fallback si la map n'est pas trouvée
        x, y = entry_positions.get(last_map, default_position)
        
        # Pour creer le joueur
        self.player_sprite = Player.load_player(x, y, self.quest_manager)
        self.scene.add_sprite("Player", self.player_sprite)   # ajoute le joueur à la liste des éléments de la scene

        # Creer les PNJs
        pnj = Humain(charisme=0.3, rigidite=0.3, beauf=0.3, receptif_beauf=0.3)
        louis = PNJ("Mael", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        louis.center_x = 694
        louis.center_y = 940
        mael = PNJ("Louis", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        mael.center_x = 556
        mael.center_y = 940
        thomas = PNJ("Thomas", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        thomas.center_x = 556 
        thomas.center_y = 790
        kyle = PNJ("Kyle", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        kyle.center_x = 694 
        kyle.center_y = 790
        self.pnj_sprite.append(louis)
        self.pnj_sprite.append(mael)
        self.pnj_sprite.append(thomas)
        self.pnj_sprite.append(kyle)
        self.scene.add_sprite("Pnj", louis)
        self.scene.add_sprite("Pnj", mael)
        self.scene.add_sprite("Pnj", thomas)
        self.scene.add_sprite("Pnj", kyle)

        # Creer les strategiques
        hotesse = PNJ("Hotesse", pnj, "Femelle", "assets/images/hotesse_l.png", PLAYER_SCALING)
        hotesse.center_x = 2850 
        hotesse.center_y = 1848
        self.strategique_sprite.append(hotesse)
        self.scene.add_sprite("Pnj", hotesse)

        # Creer les objets
        livre = UpStat("assets/images/livre.png", 0.7, "Pythagore", "mathematique")
        livre.center_x = 448
        livre.center_y = 1030
        self.objet_sprites.append(livre)
        self.scene.add_sprite("Livre", livre)

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

        # Fonctions déclarées dans BaseGameView :

        # Pour interagir avec les objets
        self.interact.interact_obj_prg()

        # Pour interagir avec les strategiques
        self.interact.interact_pnj_strateg()
            
        # Pour dialoguer avec les PNJ
        self.interact.interact_pnj()   

        # Pour aller dans d'autres map
        if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
            left, top = self.interact.draw_interact_box()
            arcade.draw_text("RALT : Maison", left + 15, top - 30, arcade.color.LIGHT_GREEN, 14)

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

        # Pour changer de map
        if self.current_strategique and key == arcade.key.RALT:
            self.player_sprite.save_player()
            self.manager.switch_map("tma")

        if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600 and key == arcade.key.RALT:
            self.player_sprite.save_player()
            self.manager.switch_map("home")   
    
    def on_key_release(self, key, modifiers):
        self.keycaps.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()

    def charger_stats(chemin_fichier="save/stats.json"):
        with open(chemin_fichier, "r") as f:
            data = json.load(f)
        return Humain.from_dict(data)    
    

