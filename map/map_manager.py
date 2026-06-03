from __future__ import annotations
import arcade
import os
from dotenv import load_dotenv
from map.map_classes.environnement import Environnement
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, KENNY
from map.map_classes.HOME import GameView as homeview
from map.map_classes.PHL import GameView as phlview
from map.map_classes.TMA import GameView as tmaview

load_dotenv()

_MAPS = {
    "home": homeview,
    "phl": phlview,
    "tma": tmaview,
}

_travail = Environnement("Bureau", tension_sociale=0.7, densite_sociale=0.5, regles_sociale="formelles")
_bar = Environnement("Bar", tension_sociale=0.2, densite_sociale=0.8, regles_sociale="informelles")


class LoadingView(arcade.View):
    """Affiche 'Chargement...' pendant un frame avant d'exécuter le setup de la map."""

    def __init__(self, setup_fn):
        super().__init__()
        self._setup_fn = setup_fn
        self._ready = False

    def on_draw(self) -> None:
        self.clear()
        arcade.draw_text(
            "Chargement...",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
            arcade.color.WHITE, 28,
            anchor_x="center", anchor_y="center",
            font_name=KENNY,
        )

    def on_update(self, delta_time: float) -> None:
        if not self._ready:
            self._ready = True
        else:
            self._setup_fn()


class MapManager:
    def __init__(self, quest_manager, character_manager):
        self.window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=False)
        self.environnement = _travail
        self.quest_manager = quest_manager
        self.character_manager = character_manager
        self.last_map: str | None = None
        self.current_map = "home"
        self.view = None
        self._load_initial_map()

    def _load_initial_map(self) -> None:
        def do_setup():
            view = homeview(self.environnement, self.quest_manager, self.character_manager)
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
            view = view_class(self.environnement, self.quest_manager, self.character_manager)
            view.set_manager(self)
            view.setup(self.last_map)
            self.view = view
            self.window.show_view(view)

        loading = LoadingView(do_setup)
        self.window.show_view(loading)
