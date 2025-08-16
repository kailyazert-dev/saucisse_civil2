import arcade
import os
from map.map_classes.environnement import Environnement
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, MOVEMENT_SPEED
from map.map_classes.HOME import GameView as homeview
from map.map_classes.PHL import GameView as phlview
from map.map_classes.TMA import GameView as tmaview
from dotenv import load_dotenv

maps = {
    "home" : homeview,
    "phl" : phlview,
    "tma" : tmaview
}
# Création d'une instance d'Environnement
travaille = Environnement("Bureau", tension_sociale=0.7, densite_sociale=0.5, regles_sociale="formelles")
bar = Environnement("Bar", tension_sociale=0.2, densite_sociale=0.8, regles_sociale="informelles")

window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=False)

load_dotenv()
API_KEY = os.getenv("REPLICATE_API_TOKEN")

class MapManager:

    def __init__(self, quest_manager, character_manager):
        self.window = window
        self.environnement = travaille
        self.quest_manager = quest_manager
        self.character_manager = character_manager
        self.last_map = None
        self.current_map = "home"
        self.view = None
        self.load_initial_map()

    def load_initial_map(self):
        self.view = homeview(self.environnement, self.quest_manager, self.character_manager)
        self.view.set_manager(self)
        self.view.setup(self.last_map)
        self.window.show_view(self.view)    

    def switch_map(self, map_name):
        self.last_map = self.current_map
        self.current_map = map_name
        self.view = maps[map_name](self.environnement, self.quest_manager, self.character_manager)

        self.view.set_manager(self)
        self.view.setup(self.last_map)
        self.window.show_view(self.view)    