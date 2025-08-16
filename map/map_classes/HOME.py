import arcade
import os
from map.map_classes.objet import UpStat, UpStatCollection
from map.map_base import BaseGameView
# from character.character_manager import CharacterManager

class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)
        self.quest_manager = quest_manager
        self.character_manager = character_manager

    """ Configuration de la map """
    def setup(self, last_map):
        # Chemin du fichier
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Chemin pour arriver au dosssier ou est situer le fichier home
        self.home_file_dir = os.path.join(self.base_dir, "../map_tmx")
        # Chemin pour acceder au fichier home
        self.map_home = os.path.join(self.home_file_dir, "HOME.tmx")

        # Charger la carte TMX
        self.tile_map = arcade.load_tilemap(self.map_home, scaling=1.0) # tile_map est dans BaseGameView

        # Créer la scène à partir de la tilemap
        self.scene = arcade.Scene.from_tilemap(self.tile_map) # scene est dans BaseGameView

        # Vérifie si l'arc 1 est terminer (renvoie true si oui)
        self.arc1_t = self.quest_manager.arc.status == 't'
        
        # récupère le joueur
        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x = 745
        self.player_sprite.center_y = 970

        # self.player_sprite = self.character_manager.load_player(745, 970, self.quest_manager)     # create_player est dans BaseGameView
        self.scene.add_sprite("Player", self.player_sprite)    # ajoute le joueur à la liste des éléments de la scene

        # Creer les PNJs

        # Creer les strategiques

        # Creer les objets
        livre1 = UpStat("assets/images/bibliotheque.png", 1, "Multiplication", "mathematique", 0, 0.15)
        livre2 = UpStat("assets/images/bibliotheque.png", 1, "Addition", "mathematique", 0, 0.11)
        self.objet_sprites.append(livre1)
        self.objet_sprites.append(livre2)

        bibliothèque = UpStatCollection("assets/images/bibliotheque.png", 1, "Bibliothèque")
        bibliothèque.add_upStats(livre1)
        bibliothèque.add_upStats(livre2)
        bibliothèque.center_x = 1104
        bibliothèque.center_y = 627
        self.objet_sprites.append(bibliothèque)
        self.scene.add_sprite("Bibliothèque", bibliothèque)

        ordinateur = UpStat("assets/images/ordinateur.png", 1, "Jeu échec", "logique", 0, 0.16)
        ordinateur.center_x =  73
        ordinateur.center_y =  667
        self.objet_sprites.append(ordinateur)
        self.scene.add_sprite("Ordinateur", ordinateur)

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

        # Pour aller à PHL (à condition d'avoir reusit la premiere quête)
        if self.arc1_t :
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750 :
                left, top = self.interact.draw_interact_box()
                arcade.draw_text("RALT : PHL", left + 15, top - 30, arcade.color.LIGHT_GREEN, 14) 

        # Déssine la camera
        self.camera_gui.use()  

        # Pour la stat_box
        self.interact.draw_box()  

        # Pour avoir position du joueur sur la carte
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

    """ Fonction pour gérer les clicks souris """
    def on_mouse_press(self, x, y, button, modifiers):
        self.keycaps.on_mouse_press(x, y, button, modifiers)

    """ Fonction pour gérer les touches """
    def on_key_press(self, key, modifiers):

        # Apelle les fonctions de base
        self.keycaps.handle_key_press(key, modifiers) 

        # Pour aller à PHL (à condition d'avoir réussit la quête 1)
        if self.arc1_t:
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750 and key == arcade.key.RALT:
                self.player_sprite.save_player()
                self.manager.switch_map("phl")
    
    def on_key_release(self, key, modifiers):
        self.keycaps.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
    

