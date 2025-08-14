import arcade
from map.home.HOME import GameView as homeview
from map.armonie.PHL import GameView as phlview
from map.armonie.TMA import GameView as tmaview

maps = {
    "home" : homeview,
    "phl" : phlview,
    "tma" : tmaview
}
class MapManager:
    def __init__(self, window, environnement_instance, quest_manager):
        self.window = window
        self.environnement = environnement_instance
        self.quest_manager = quest_manager
        self.last_map = None
        self.current_map = "home"
        self.view = None

    def load_initial_map(self):
        self.view = homeview(self.environnement, self.quest_manager)
        self.view.set_manager(self)
        self.view.setup(self.last_map)
        self.window.show_view(self.view)    

    def switch_map(self, map_name):
        self.last_map = self.current_map
        self.current_map = map_name
        self.view = maps[map_name](self.environnement, self.quest_manager)

        self.view.set_manager(self)
        self.view.setup(self.last_map)
        self.window.show_view(self.view)    
