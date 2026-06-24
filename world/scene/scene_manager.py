from __future__ import annotations
import arcade
import os
from dotenv import load_dotenv
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, KENNY
from world.scene.loading_view import LoadingView
from world.maps.home_scene import HomeScene as homeview
from world.maps.phl_scene import PhlScene as phlview
from world.maps.tma_scene import TmaScene as tmaview
from merc.merc_scene import MercScene as mercview

load_dotenv()

_MAPS = {
    "home": homeview,
    "phl":  phlview,
    "tma":  tmaview,
    "merc": mercview,
}


class SceneManager:
    def __init__(self, quest_manager, character_manager):
        self.window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=False)
        self.quest_manager = quest_manager
        self.character_manager = character_manager
        self.last_map: str | None = None
        self.current_map = "home"
        self.view = None
        self._load_initial_map()

    def _load_initial_map(self) -> None:
        def do_setup():
            view = homeview(None, self.quest_manager, self.character_manager)
            view.set_manager(self)
            view.setup(self.last_map)
            self.view = view
            self.window.show_view(view)

        loading = LoadingView(do_setup)
        self.window.show_view(loading)

    def switch_map(self, map_name: str) -> None:
        self.last_map = self.current_map
        self.current_map = map_name

        def do_setup():
            view_class = _MAPS[map_name]
            view = view_class(None, self.quest_manager, self.character_manager)
            view.set_manager(self)
            view.setup(self.last_map)
            self.view = view
            self.window.show_view(view)

        loading = LoadingView(do_setup)
        self.window.show_view(loading)
