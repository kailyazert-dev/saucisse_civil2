import arcade
import json
import os
from classes.humain import Humain, PNJ, Player
from classes.objet import Objet, Progresseur
from assets.param_map import PLAYER_SCALING
from map.map_base import BaseGameView
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT

class GameView(BaseGameView):
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
        self.player_sprite = Player.load_player(x, y)
        self.scene.add_sprite("Player", self.player_sprite)   # ajoute le joueur à la liste des éléments de la scene

        # Creer les PNJs
        pnj = Humain(charisme=0.3, rigidite=0.3, beauf=0.3, receptif_beauf=0.3)
        louis = PNJ("Mael", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        louis.center_x = 556
        louis.center_y = 940
        mael = PNJ("Louis", pnj, "Male", "assets/images/player_d.png", PLAYER_SCALING)
        mael.center_x = 694 
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
        livre = Progresseur("assets/images/livre.png", 0.7, "Pythagore", "mathematique")
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

        # Pour interagir avec les objets
        for objet in self.objet_sprites:
            distance = arcade.get_distance_between_sprites(self.player_sprite, objet)
            if distance < 48:
                self.current_objet = objet
                arcade.draw_text("ENTER : utiliser", self.player_sprite.center_x - 40, self.player_sprite.center_y - 40, arcade.color.LIGHT_GREEN, 18)

        # Pour interagir avec les strategiques
        for strategique in self.strategique_sprite:
            distance = arcade.get_distance_between_sprites(self.player_sprite, strategique)
            if distance < 92:
                self.current_strategique = strategique
                arcade.draw_text("RALT : Aller à la PHL", strategique.center_x - 40, strategique.center_y - 40, arcade.color.LIGHT_GREEN, 18) 
                arcade.draw_text(strategique.get_nom(), strategique.center_x - 40, strategique.center_y + 40, arcade.color.ALLOY_ORANGE, 18) 
                break
            
        # Pour dialoguer avec les PNJ
        for pnj in self.pnj_sprite:
            distance = arcade.get_distance_between_sprites(self.player_sprite, pnj)
            if distance < 50:
               arcade.draw_text("LALT : Discuter", pnj.center_x - 40, pnj.center_y - 40, arcade.color.LIGHT_GREEN, 18) 
               arcade.draw_text(pnj.get_nom(), pnj.center_x - 40, pnj.center_y + 40, arcade.color.ALLOY_ORANGE, 18) 
            if self.is_typing and self.current_pnj:
               self.draw_dialogue_box()    # Fonction déclarer dans BaseGameView

        # Déssine la camera
        self.camera_gui.use()    

        # Pour avoir la position du joueur sur la carte
        self.get_position()        # Fonction déclarer dans BaseGameView 

        if 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600:
            arcade.draw_text("RALT : Home", WINDOW_WIDTH // 2 - 70 , WINDOW_HEIGHT // 2 - 60, arcade.color.LIGHT_GREEN, 18)  


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

        # Pour arreter l'augmentation de la force
        if self.current_objet and key in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.current_objet = None   
            self.player_sprite.stop_up() 

        # Déplacements généraux
        if self.handle_movement_keys(key):  # Fontion déclarer dans BaseGameView 
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
                self.last_response = self.talk_model(self.current_input, self.current_pnj)
            self.current_input = ""

        elif self.is_typing and key == arcade.key.BACKSPACE:
            self.current_input = self.current_input[:-1]

        # Pour changer de map
        elif self.current_strategique and key == arcade.key.RALT:
            self.player_sprite.save_player()
            self.manager.switch_map("tma")

        elif 0 <= self.player_sprite.center_y <= 55 and 550 <= self.player_sprite.center_x <= 600 and key == arcade.key.RALT:
            self.player_sprite.save_player()
            self.manager.switch_map("home")   

        # pour upgrade les stats
        elif self.current_objet and key == arcade.key.ENTER:
            print('Niveau en mathématique :')
            self.player_sprite.start_up(self.current_objet.stat_cible)    
    
    def on_key_release(self, key, modifiers):
        self.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()

    def charger_stats(chemin_fichier="save/stats.json"):
        with open(chemin_fichier, "r") as f:
            data = json.load(f)
        return Humain.from_dict(data)    
    

