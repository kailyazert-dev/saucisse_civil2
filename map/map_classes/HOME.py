from __future__ import annotations
import arcade
from assets.param_map import KENNY
from map.map_classes.objet import UpStat, UpStatCollection, MapActionObject
from map.map_base import BaseGameView
import utils.paths as paths

class GameView(BaseGameView):

    def __init__(self, environnement, quest_manager, character_manager):
        super().__init__(environnement, quest_manager, character_manager)
        self.quest_manager = quest_manager
        self.character_manager = character_manager

    """ Configuration de la map """
    def setup(self, last_map):
        self.tile_map = arcade.load_tilemap(paths.asset("map/map_tmx/HOME.tmx"), scaling=1.0)

        # Créer la scène à partir de la tilemap
        self.scene = arcade.Scene.from_tilemap(self.tile_map) # scene est dans BaseGameView

        # récupère le joueur et le place
        self.player_sprite = self.character_manager.player
        self.player_sprite.center_x = 745
        self.player_sprite.center_y = 970

        # self.player_sprite = self.character_manager.load_player(745, 970, self.quest_manager)     # create_player est dans BaseGameView
        self.scene.add_sprite("Player", self.player_sprite)    # ajoute le joueur à la liste des éléments de la scene

        # Creer les PNJs

        # Creer les strategiques

        # Creer les objets
        livre1 = UpStat(paths.asset("map/map_tmx/livre.png"), 1, "Multiplication", "mathematique", 0.14, 0.19)
        livre2 = UpStat(paths.asset("map/map_tmx/livre.png"), 1, "Addition", "mathematique", 0, 0.14)

        bibliothèque = UpStatCollection(paths.asset("assets/images/bibliotheque.png"), 1, "Bibliothèque")
        bibliothèque.add_upStats(livre1)
        bibliothèque.add_upStats(livre2)
        bibliothèque.center_x = 1104
        bibliothèque.center_y = 627
        self.objet_sprites.append(bibliothèque)
        self.scene.add_sprite("Bibliothèque", bibliothèque)

        # PC — Jeu d'échec (quest 1 : logique 0 → 0.16)
        ordinateur = UpStat(paths.asset("assets/images/ordinateur.png"), 1, "Jeu d'echec", "logique", 0, 0.16)
        ordinateur.center_x = 73
        ordinateur.center_y = 667
        self.objet_sprites.append(ordinateur)
        self.scene.add_sprite("Ordinateur", ordinateur)

        # PC — Envoyer son CV sur Indeed (quest 2, objectif 2)
        ordinateur_indeed = MapActionObject(paths.asset("assets/images/ordinateur.png"), 1, "Envoyer sur Indeed", "envoyer son cv sur indead")
        ordinateur_indeed.center_x = 73
        ordinateur_indeed.center_y = 667
        self.objet_sprites.append(ordinateur_indeed)

        # PC — Rédiger son CV (quest 2, objectif 1)
        ordinateur_cv = MapActionObject(paths.asset("assets/images/ordinateur.png"), 1, "Rediger son CV", "rediger son cv")
        ordinateur_cv.center_x = 73
        ordinateur_cv.center_y = 667
        self.objet_sprites.append(ordinateur_cv)

        # PC — Consulter ses mails (quest 3, objectif 1)
        ordinateur_mails = MapActionObject(paths.asset("assets/images/ordinateur.png"), 1, "Consulter ses mails", "Consulté tes mails.")
        ordinateur_mails.center_x = 73
        ordinateur_mails.center_y = 667
        self.objet_sprites.append(ordinateur_mails)

        # PC — Répondre à l'offre (quest 3, objectif 2)
        ordinateur_offre = MapActionObject(paths.asset("assets/images/ordinateur.png"), 1, "Repondre a l'offre", "Répondre à l'offre.")
        ordinateur_offre.center_x = 73
        ordinateur_offre.center_y = 667
        self.objet_sprites.append(ordinateur_offre)

        # Creer les obstacles
        obstacles = self.interact.create_obstacles()

        # Moteur physique sur les element de la map
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            obstacles
        )

    @property
    def _phl_unlocked(self) -> bool:
        """Accessible uniquement à partir de l'arc 2."""
        arc = self.quest_manager.arc
        if arc is None:
            return True  # Plus d'arcs = jeu terminé, accès libre
        return arc.arc_id >= 2

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
        if self._phl_unlocked :
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750 :
                left, top = self.interact.draw_interact_box()
                arcade.draw_text("RALT : PHL", left + 15, top - 30, arcade.color.LIGHT_GREEN, 14, font_name=KENNY) 

        # Déssine la camera
        self.camera_gui.use()

        # Pour la stat_box
        self.interact.draw_box()

        self.get_quests()
        self.interact.draw_side_bar()
        self.get_position()
        self.draw_notif()
        self.menu.draw()

    """Fonction pour ecrire le dialogue"""
    def on_text(self, text):
        if self.is_typing:
            self.talk.on_text(text)
            
    """ Fonction qui met à jour la map """
    def on_update(self, delta_time):
        self.physics_engine.update()
        self.scene.update(delta_time)
        self.follow_player()
        self.update_notif(delta_time)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        self.keycaps.on_mouse_press(x, y, button, modifiers)

    """ Fonction pour gérer les touches """
    def on_key_press(self, key, modifiers):

        # Apelle les fonctions de base
        self.keycaps.handle_key_press(key, modifiers) 

        # Pour aller à PHL (à condition d'avoir réussit la quête 1)
        if self._phl_unlocked:
            if 975 <= self.player_sprite.center_y <= 980 and 740 <= self.player_sprite.center_x <= 750 and key == arcade.key.RALT:
                self.character_manager.save_player()
                self.manager.switch_map("phl")
    
    def on_key_release(self, key, modifiers):
        self.keycaps.reset_movement_on_release(key, modifiers)

    """ Fonction pour redimensionner la fenêtre """
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
    

